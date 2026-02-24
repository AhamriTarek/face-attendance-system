import cv2
import threading
import face_recognition
import numpy as np
import datetime
from django.utils import timezone
from face_recognition_app.models import StudentFace
from face_recognition_app.utils import deserialize_embedding
from attendance.models import AttendanceRecord, Student

class VideoCamera(object):
    def __init__(self):
        # Using 0 for webcam. Ensure DSHOW for Windows if needed, or default
        self.video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.video.isOpened():
             self.video = cv2.VideoCapture(0)
             
        (self.grabbed, self.frame) = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        return self.frame

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()

class FaceRecognizerService:
    _instance = None
    _camera = None
    _is_recognition_active = True
    
    # Cache known faces
    _known_encodings = []
    _known_ids = []
    _known_names = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FaceRecognizerService, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        self._camera = VideoCamera()
        self.reload_faces()

    def reload_faces(self):
        print("Reloading faces...")
        self._known_encodings = []
        self._known_ids = []
        self._known_names = []
        
        faces = StudentFace.objects.all().select_related('student')
        for face in faces:
            try:
                enc = deserialize_embedding(face.embedding)
                self._known_encodings.append(enc)
                self._known_ids.append(face.student.id)
                self._known_names.append(face.student.full_name)
            except Exception as e:
                print(f"Error loading face {face.id}: {e}")
        print(f"Loaded {len(self._known_encodings)} faces.")

    def set_active(self, active: bool):
        self._is_recognition_active = active

    def get_frame(self, session_id):
        frame = self._camera.get_frame()
        if frame is None:
            return None
            
        # Resize for speed
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5) # 0.5 scale
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        names_detected = []

        if self._is_recognition_active:
             # Find faces
            face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                name = "Unknown"
                student_id = None
                
                if self._known_encodings:
                    distances = face_recognition.face_distance(self._known_encodings, face_encoding)
                    best_match_index = np.argmin(distances)
                    
                    if distances[best_match_index] < 0.6:
                        name = self._known_names[best_match_index]
                        student_id = self._known_ids[best_match_index]
                        
                        # Trigger Attendance Logic
                        self.mark_attendance(student_id, session_id)

                # Scale back up
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2

                # Draw
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def mark_attendance(self, student_id, session_id):
        try:
            from attendance.models import AttendanceSession
            session = AttendanceSession.objects.get(id=session_id)
            student = Student.objects.get(id=student_id)
            now = timezone.now()

            record, created = AttendanceRecord.objects.get_or_create(
                session=session,
                student=student,
                defaults={
                    'check_in': now,
                    'status': 'present', # Logic for late could go here
                    'method': 'face'
                }
            )

            if not created:
                 # Check out logic
                 if record.check_out is None:
                     if record.check_in and (now - record.check_in).total_seconds() > 60:
                         record.check_out = now
                         record.save()
        except Exception as e:
            print(f"Error marking attendance: {e}")
