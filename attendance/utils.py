import json

# NOTE: face_recognition / cv2 / numpy are imported lazily inside the methods
# below so this module can be imported on a server without those heavy
# libraries installed (cloud mode). When FACE_RECOGNITION_ENABLED is on
# (local mode) the imports succeed exactly as before.

class FaceRecognizer:
    @staticmethod
    def get_face_encoding(image_path):
        """
        Loads an image and returns the face encoding (list).
        Returns None if no face is found.
        """
        import face_recognition
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
    def recognize_faces(frame, known_encodings, known_names, tolerance=0.6):
        """
        Recognizes faces in a given frame (numpy array).
        Returns a list of names of recognized faces and their locations.
        """
        import face_recognition
        import cv2
        import numpy as np
        # Resize frame of video to 1/2 size (0.5x) for faster processing
        # Using 0.25x was too aggressive and caused issues with phone screens
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        
        # Convert the image from BGR to RGB
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        if len(face_locations) > 0:
            print(f"[DEBUG] Detected {len(face_locations)} faces in current frame.")

        face_names = []
        for face_encoding in face_encodings:
            name = "Unknown"
            
            # If known_encodings is empty, can't match anything
            if not known_encodings:
                print(f"[DEBUG] No known encodings loaded. Cannot match face.")
            else:
                # Use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                best_distance = face_distances[best_match_index]
                
                print(f"[DEBUG] Face match distance calculation - Best distance: {best_distance:.4f} (Threshold: {tolerance})")
                
                if best_distance <= tolerance:
                    name = known_names[best_match_index]
                    print(f"[DEBUG] => Match SUCCESS! Student ID: {name}")
                else:
                    print(f"[DEBUG] => Match FAILED. Best match was distance {best_distance:.4f} > {tolerance}")

            face_names.append(name)
            
        return face_locations, face_names
