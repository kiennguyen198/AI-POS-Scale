import cv2

from config import CAMERA_SOURCE,FRAME_HEIGHT,FRAME_WIDTH,SCALE_X1,SCALE_X2,SCALE_Y1,SCALE_Y2

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

def crop_scale_area(frame):
    scale_frame=frame[SCALE_Y1:SCALE_Y2,SCALE_X1:SCALE_X2]
    return scale_frame

def release_camera(cap):
    cap.release()
    
