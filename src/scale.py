from config import HX711_DT_PIN,HX711_SCK_PIN,EMPTY_WEIGHT_THRESHOLD,STABLE_WEIGHT_THRESHOLD,STABLE_SAMPLE_COUNT,MAX_WEIGHT
from statistics import median

def setup_scale():
    import RPi.GPIO as GPIO # khai báo trong hàm vì laptop không có rasp
    from hx711 import HX711 

    GPIO.setmode(GPIO.BCM) # cấu hình cách gọi chân là BCM 
    hx=HX711(HX711_DT_PIN,HX711_SCK_PIN)
    hx.reset()

    return hx

def read_raw(hx):
    raw_data=hx.get_raw_data()
    raw_value=median(raw_data)
    return raw_value

def tare_scale(hx): # raw khi cân trống
    tare_offset=read_raw(hx)
    return tare_offset

def calibrate_scale(hx,tare_offset,known_weight):
    raw_value=read_raw(hx)
    raw_diff=raw_value-tare_offset
    calibration=raw_diff/known_weight
    return calibration

def get_weight(hx,tare_offset,calibration):
    raw_value=read_raw(hx)
    raw_diff=raw_value-tare_offset
    weight=raw_diff/calibration
    return round(weight)

def is_scale_empty(weight):
    return abs(weight)<=EMPTY_WEIGHT_THRESHOLD

def update_weight_history(weights,weight): # lưu 15 giá trị cân gần nhất
    weights.append(weight)
    if len(weights)>STABLE_SAMPLE_COUNT:
        weights.pop(0)
    return weights

def is_weight_stable(weights):
    if len(weights)<STABLE_SAMPLE_COUNT:
        return False

    recent_weights=weights[-STABLE_SAMPLE_COUNT:]
    highest_weight=max(recent_weights)
    lowest_weight=min(recent_weights)
    weight_change=highest_weight-lowest_weight

    #15 lần đo (max-min)<= Weight_threshold thì cân ổn định

    if weight_change<=STABLE_WEIGHT_THRESHOLD:
        return True
    else:
        return False

def is_overloaded(weight):
    if weight>MAX_WEIGHT:
        return True
    else:
        return False

def cleanup_scale():
    import RPi.GPIO as GPIO
    GPIO.cleanup() # giải phóng các chân đã sử dụng để lần sau chạy lại không gây lỗi chương trình
