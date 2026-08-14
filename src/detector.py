from ultralytics import YOLO
from config import MODEL_PATH, CONFIDENCE_THRESHOLD,INFERENCE_IMAGE_SIZE,DETECTION_HISTORY_SIZE,DETECTION_MIN_COUNT,MIXED_HISTORY_SIZE,MIXED_MIN_COUNT

def load_model():
    model=YOLO(str(MODEL_PATH))

    return model

def detect(model,frame):
    results= model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        imgsz=INFERENCE_IMAGE_SIZE,
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

def check_single_fruit_type(fruit_names):
    return len(set(fruit_names))==1

# lưu DETECTION_HISTORY_SIZE frame gần nhất
def update_detection_history(history,fruit_names):
    history.append(fruit_names)

    if len(history)>DETECTION_HISTORY_SIZE:
        history.pop(0)

    return history

def get_stable_fruit(history):
    if len(history)<DETECTION_HISTORY_SIZE:
        return None # Nếu chưa đủ số frame trong history thì trả về None.
    valid_fruits=[]
    for frame_fruits in history:
        if check_single_fruit_type(frame_fruits): # nếu 1 frame có nhiều quả giống nhau thì chỉ lưu 1 vào valid_fruits
            fruit_name=frame_fruits[0]
            valid_fruits.append(fruit_name) # Mỗi frame chỉ có một loại sẽ thêm tên loại đó một lần vào valid_fruits.

    for fruit_name in set(valid_fruits): # set để loại bỏ giá trị trùng nhau
        if valid_fruits.count(fruit_name)>=DETECTION_MIN_COUNT:
            return fruit_name # Duyệt các tên không trùng lặp, loại nào xuất hiện đủ DETECTION_MIN_COUNT frame thì trả về tên đó.

    return None # Không loại nào đạt ngưỡng thì trả về None.

def has_multiple_fruit_types(history):
    if len(history)<MIXED_HISTORY_SIZE:
        return False

    recent_history=history[-MIXED_HISTORY_SIZE:]
    mixed_count=0

    for frame_fruits in recent_history:
        fruit_types=set(frame_fruits)
        if len(fruit_types)>=2:
            mixed_count+=1

    if mixed_count>=MIXED_MIN_COUNT:
        return True
    else:
        return False
