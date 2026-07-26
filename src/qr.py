from datetime import datetime
import qrcode
def create_label_id():
    current_time=datetime.now()
    label_id="L"+current_time.strftime("%Y%m%d%H%M%S%f")
    return label_id

def create_qr_data(label_id,fruit_name,weight_g,price_per_kg):
    qr_data=f"AI_POS|1|{label_id}|{fruit_name}|{weight_g}|{price_per_kg}"
    return qr_data

def create_qr_image(qr_data):
    qr_image=qrcode.make(qr_data)
    return qr_image
