import cv2
from config import CAMERA_SOURCE
def open_camera():
    cap=cv2.VideoCapture(CAMERA_SOURCE)
    return cap

def get_frame(cap):
    ret,frame=cap.read()
    if not ret:
        return None
    return frame

def release_camera(cap):
    cap.release()
    
