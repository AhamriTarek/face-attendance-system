from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import face_recognition
import numpy as np
from face_recognition_app.models import StudentFace
from face_recognition_app.utils import deserialize_embedding
from accounts.models import Student

class RecognizeFaceAPI(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        if 'image' not in request.files:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.files['image']
        
        try:
            # Load image from upload
            image = face_recognition.load_image_file(image_file)
            
            # Find face in uploaded image
            face_locations = face_recognition.face_locations(image)
            if not face_locations:
                return Response({'match': False, 'message': 'No face detected'}, status=200)

            # Encode
            unknown_encodings = face_recognition.face_encodings(image, face_locations)
            if not unknown_encodings:
                return Response({'match': False, 'message': 'Could not encode face'}, status=200)

            unknown_encoding = unknown_encodings[0]

            # Fetch all known faces
            # OPTIMIZATION: In production, cache this or use a vector DB.
            known_faces = StudentFace.objects.all()
            
            if not known_faces.exists():
                return Response({'match': False, 'message': 'No registered students'}, status=200)

            known_encodings = []
            student_ids = []

            for kf in known_faces:
                try:
                    encoding = deserialize_embedding(kf.embedding)
                    known_encodings.append(encoding)
                    student_ids.append(kf.student_id)
                except:
                    continue
            
            if not known_encodings:
                return Response({'match': False}, status=200)
                
            # Compare
            distances = face_recognition.face_distance(known_encodings, unknown_encoding)
            best_match_index = np.argmin(distances)
            
            if distances[best_match_index] < 0.50:
                matched_student_id = student_ids[best_match_index]
                student = Student.objects.get(id=matched_student_id)
                
                # Mark Attendance if session_id is present
                session_id = request.data.get('session_id')
                attendance_status = "Identified"
                
                if session_id:
                    from attendance.models import AttendanceSession, AttendanceRecord
                    from django.utils import timezone
                    import datetime
                    
                    try:
                        session = AttendanceSession.objects.get(id=session_id)
                        
                        # Logic:
                        # 1. No record -> Create (Check-in)
                        # 2. Record exists, no check_out, time > 1 min -> Check-out
                        # 3. Record exists, check_out exists -> Already done
                        
                        now = timezone.now()
                        
                        record, created = AttendanceRecord.objects.get_or_create(
                            session=session,
                            student=student,
                            defaults={
                                'check_in': now,
                                'status': 'present',
                                'method': 'face'
                            }
                        )
                        
                        if created:
                            attendance_status = f"Checked IN ({student.full_name})"
                        else:
                            # If checked in, check for check out
                            if record.check_out is None:
                                # Prevent double bounce (wait 1 minute before check out)
                                if record.check_in and (now - record.check_in).total_seconds() > 60:
                                    record.check_out = now
                                    record.save()
                                    attendance_status = f"Checked OUT ({student.full_name})"
                                else:
                                    attendance_status = f"Already Checked IN ({student.full_name})"
                            else:
                                attendance_status = f"Already Completed ({student.full_name})"

                    except AttendanceSession.DoesNotExist:
                        pass

                return Response({
                    'match': True,
                    'student_id': student.id,
                    'student_name': student.full_name,
                    'confidence': float(1 - distances[best_match_index]),
                    'status': attendance_status
                }, status=200)
            else:
                return Response({'match': False, 'message': 'Unknown person'}, status=200)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
