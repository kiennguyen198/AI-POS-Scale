import cv2

from config import CAMERA_SOURCE,FRAME_HEIGHT,FRAME_WIDTH

def open_camera():
    cap=cv2.VideoCapture(CAMERA_SOURCE)
    
    if not cap.isOpened():
        cap.release()
        raise RuntimeError("Không thể mở camera")
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,FRAME_HEIGHT)

    return cap

def get_frame(cap):
    ret,frame=cap.read()
    if not ret:
        return None
    return frame

def release_camera(cap):
    cap.release()
    
