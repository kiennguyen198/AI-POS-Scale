# hằng số cấu hình viết in hoa
import sys
from pathlib import Path

# Root
PROJECT_ROOT=Path(__file__).resolve().parent.parent

# Camera
# Webcam mặc định dùng khi chạy thử trên laptop.
LAPTOP_CAMERA_SOURCE = 0

# Pi Camera V2 dùng qua Picamera2 trên Raspberry Pi OS.
PI_CAMERA_SOURCE = "picamera2"

# Tự chọn camera theo thiết bị chạy chương trình.
CUSTOMER_CAMERA_SOURCE = (
    PI_CAMERA_SOURCE if sys.platform.startswith("linux") else LAPTOP_CAMERA_SOURCE
)
CASHIER_CAMERA_SOURCE = LAPTOP_CAMERA_SOURCE
FRAME_WIDTH=640
FRAME_HEIGHT=480
# Vùng mặt cân trong hình camera
SCALE_X1=80
SCALE_Y1=60
SCALE_X2=560
SCALE_Y2=420

# AI
MODEL_PATH=PROJECT_ROOT/'models'/'best.pt'
CONFIDENCE_THRESHOLD=0.5
INFERENCE_IMAGE_SIZE=320

DETECTION_HISTORY_SIZE=15 # nhận 15 frame
DETECTION_MIN_COUNT=10  # tên quả nào xuất hiện ít nhất 10/15 frame thì trả về

MIXED_HISTORY_SIZE=5 # kiểm tra 5 frame xem có mấy loại quả
MIXED_MIN_COUNT=3 # nếu ít nhất 3/5 frame có từ 2 loại quả khác nhau thì cảnh báo
# Database
DATABASE_PATH=PROJECT_ROOT/'database'/'fruits.db'

# Scale
HX711_DT_PIN=5
HX711_SCK_PIN=6
EMPTY_WEIGHT_THRESHOLD=20
STABLE_SAMPLE_COUNT=15
STABLE_WEIGHT_THRESHOLD=5
MAX_WEIGHT=5000

# QR scanner
QR_RELEASE_FRAME_COUNT=5
