import cv2
import numpy as np
import os

def detect_faces(image):
    """
    Detects faces in an image using OpenCV's Haar cascades.
    Returns a list of bounding boxes (x, y, w, h).
    If no faces are detected, returns a bounding box for the entire image.
    """
    # OpenCV's default Haar cascade for frontal face
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Convert to grayscale for detection if it's a color image
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
        
    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    # If no faces, fall back to full image
    if len(faces) == 0:
        h, w = image.shape[:2]
        return [(0, 0, w, h)]
        
    return faces
