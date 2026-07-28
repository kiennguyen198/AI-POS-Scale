import cv2
from config import QR_RELEASE_FRAME_COUNT
qr_detector=cv2.QRCodeDetector()

def read_qr(frame):
    qr_data,qr_points,qr_image=qr_detector.detectAndDecode(frame)
    return qr_data,qr_points

def parse_qr_data(qr_data): # đọc dữ liệu từ QR
    qr_parts=qr_data.split("|")

    if len(qr_parts)!=6:
        return None

    system_name,version,label_id,fruit_name,weight_text,price_text=qr_parts

    if system_name!="AI_POS" or version!="1":
        return None

    if label_id=="" or fruit_name=="":
        return None

    if not weight_text.isdigit() or not price_text.isdigit():
        return None

    weight_g=int(weight_text)
    price_per_kg=int(price_text)

    if weight_g<=0 or price_per_kg<=0:
        return None

    product={
        "label_id":label_id,
        "fruit_name":fruit_name,
        "weight_g":weight_g,
        "price_per_kg":price_per_kg
    }

    return product

def scan_frame(frame):
    qr_data,qr_points=read_qr(frame)
    if qr_data=="":
        return None,qr_points

    product=parse_qr_data(qr_data)

    return product,qr_points

def update_scan_state(product,qr_points,scan_locked,no_qr_frames):
    should_add=False
    qr_detected=qr_points is not None

    if qr_detected:
        no_qr_frames=0

        if product is not None and not scan_locked:
            should_add=True
            scan_locked=True

    elif scan_locked:
        no_qr_frames+=1

        if no_qr_frames>=QR_RELEASE_FRAME_COUNT:
            scan_locked=False
            no_qr_frames=0

    return should_add,scan_locked,no_qr_frames
