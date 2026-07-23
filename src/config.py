from pathlib import Path

# root
PROJECT_ROOT=Path(__file__).resolve().parent.parent

# camera
CAMERA_SOURCE=0
FRAME_WIDTH=640
FRAME_HEIGHT=480

# AI
MODEL_PATH=PROJECT_ROOT/'models'/'best.pt'
CONFIDENCE_THRESHOLD=0.5

# Database
DATABASE_PATH=PROJECT_ROOT/'database'/'fruits.db'

# Scale
HX711_DT_PIN=5
HX711_SCK_PIN=6