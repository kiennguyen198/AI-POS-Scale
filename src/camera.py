import os

import cv2

from config import FRAME_HEIGHT,FRAME_WIDTH,SCALE_X1,SCALE_X2,SCALE_Y1,SCALE_Y2

def open_camera(source):
    if os.name=="nt" and isinstance(source,int):
        cap=cv2.VideoCapture(source,cv2.CAP_DSHOW)
    else:
        cap=cv2.VideoCapture(source)
    
    if not cap.isOpened():
        cap.release()
        raise RuntimeError("Không thể mở camera")
    
    return cap

def get_frame(cap):
    ret,frame=cap.read()
    if not ret:
        return None
    frame=cv2.resize(frame,(FRAME_WIDTH,FRAME_HEIGHT))
    return frame

def crop_scale_area(frame):
    scale_frame=frame[SCALE_Y1:SCALE_Y2,SCALE_X1:SCALE_X2]
    return scale_frame

def release_camera(cap):
    cap.release()
    
