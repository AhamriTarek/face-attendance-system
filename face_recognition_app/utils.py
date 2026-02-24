import face_recognition
import pickle
import os
import cv2
import numpy as np

def get_face_embedding(image_path, model='hog'):
    """
    Generates a face embedding for a given image path.
    Returns: (embedding_bytes, error_message)
    """
    try:
        # Load image
        image = face_recognition.load_image_file(image_path)
        
        # Get face locations
        # model can be 'hog' or 'cnn'
        face_locations = face_recognition.face_locations(image, model=model)
        
        if not face_locations:
            return None, "No face found"
        
        if len(face_locations) > 1:
            return None, "Multiple faces found"
            
        # Get encoding
        # We assume the first face is the student
        encodings = face_recognition.face_encodings(image, face_locations)
        
        if not encodings:
            return None, "Could not encode face"
            
        return encodings[0], None
        
    except Exception as e:
        return None, str(e)

def serialize_embedding(embedding):
    """
    Converts numpy array embedding to bytes for database storage.
    """
    return pickle.dumps(embedding)

def deserialize_embedding(embedding_bytes):
    """
    Converts database bytes back to numpy array.
    """
    return pickle.loads(embedding_bytes)
