import face_recognition
import cv2
import numpy as np
import json

class FaceRecognizer:
    @staticmethod
    def get_face_encoding(image_path):
        """
        Loads an image and returns the face encoding (list).
        Returns None if no face is found.
        """
        try:
            image = face_recognition.load_image_file(image_path)
            # Find all face encodings in the current image
            encodings = face_recognition.face_encodings(image)
            if len(encodings) > 0:
                return encodings[0].tolist() # Convert numpy array to list for storage
            return None
        except Exception as e:
            print(f"Error processing image {image_path}: {e}")
            return None

    @staticmethod
    def recognize_faces(frame, known_encodings, known_names):
        """
        Recognizes faces in a given frame (numpy array).
        Returns a list of names of recognized faces and their locations.
        """
        # Resize frame of video to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        # Handle different OpenCV versions if needed, but usually BGR2RGB is standard
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            # See if the face is a match for the known face(s)
            
            # If known_encodings is empty, can't match anything
            if not known_encodings:
                name = "Unknown"
            else:
                matches = face_recognition.compare_faces(known_encodings, face_encoding)
                name = "Unknown"

                # Use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_names[best_match_index]

            face_names.append(name)
            
        return face_locations, face_names
