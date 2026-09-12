import os
import threading
import time

import cv2

from config import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    SCALE_X1,
    SCALE_X2,
    SCALE_Y1,
    SCALE_Y2,
)


def open_camera(source):
    if source == "picamera2":
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_video_configuration(
            main={
                "size": (FRAME_WIDTH, FRAME_HEIGHT),
                "format": "RGB888",
            }
        )
        camera.configure(config)
        camera.start()
        time.sleep(1)
        return camera

    if os.name == "nt" and isinstance(source, int):
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        cap.release()
        raise RuntimeError("Không thể mở camera")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    return cap


def _read_camera_frame(camera):
    if camera.__class__.__name__ == "Picamera2":
        frame = camera.capture_array()
        # Picamera2's RGB888 buffer is laid out as BGR in memory, which is
        # already the channel order expected by OpenCV and Ultralytics.
        # Do not convert it here or red/blue will be swapped.
        return frame

    ret, frame = camera.read()

    if not ret:
        return None

    return frame


def get_frame(camera):
    frame = _read_camera_frame(camera)

    if frame is None:
        return None

    return resize_frame(frame)


def start_latest_frame_reader(source):
    reader = {
        "cap": open_camera(source),
        "frame": None,
        "start_time": time.monotonic(),
        "last_frame_time": 0,
        "lock": threading.Lock(),
        "running": True,
        "thread": None,
    }

    reader["thread"] = threading.Thread(
        target=_read_latest_frame,
        args=(reader,),
        daemon=True,
    )
    reader["thread"].start()

    return reader


def _read_latest_frame(reader):
    while reader["running"]:
        try:
            frame = _read_camera_frame(reader["cap"])
        except Exception:
            frame = None

        if frame is None:
            time.sleep(0.05)
            continue

        with reader["lock"]:
            reader["frame"] = frame
            reader["last_frame_time"] = time.monotonic()


def get_latest_frame(reader, max_age_seconds=2):
    with reader["lock"]:
        frame = reader["frame"]
        last_frame_time = reader["last_frame_time"]

        if frame is not None:
            frame = frame.copy()

    if frame is None:
        return None

    if time.monotonic() - last_frame_time > max_age_seconds:
        return None

    return resize_frame(frame)


def resize_frame(frame):
    frame_height, frame_width = frame.shape[:2]

    if frame_width == FRAME_WIDTH and frame_height == FRAME_HEIGHT:
        return frame

    return cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))


def is_reader_starting(reader, timeout_seconds=5):
    with reader["lock"]:
        has_frame = reader["frame"] is not None

    elapsed = time.monotonic() - reader["start_time"]
    return not has_frame and elapsed < timeout_seconds


def crop_scale_area(frame):
    return frame[SCALE_Y1:SCALE_Y2, SCALE_X1:SCALE_X2]


def release_camera(camera):
    if camera.__class__.__name__ == "Picamera2":
        camera.stop()
    else:
        camera.release()


def stop_latest_frame_reader(reader):
    reader["running"] = False
    release_camera(reader["cap"])

    thread = reader["thread"]

    if thread is not None and thread.is_alive():
        thread.join(timeout=1)
