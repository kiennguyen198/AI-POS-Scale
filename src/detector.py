from ultralytics import YOLO
from config import MODEL_PATH, CONFIDENCE_THRESHOLD

def load_model():
    model=YOLO(str(MODEL_PATH))

    return model

def detect(model,frame):
    results= model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False, # không in chi tiết vào terminal
    )
    return results

def get_fruit_names(results):
    result=results[0]
    boxes=result.boxes
    fruit_names=[]

    for box in boxes:
        class_id=int(box.cls[0])
        class_name=result.names[class_id]
        fruit_names.append(class_name)

    return fruit_names

def has_fruit(fruit_names):
    return len(fruit_names) > 0

def check_single_fruit_type(fruit_names):
    return len(set(fruit_names))==1