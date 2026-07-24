# mọi thứ gặp nhau ở main, main điều phối, và các module không được biết nhau
import cv2
import camera 
import detector
import database
import scale
cap=camera.open_camera()
model=detector.load_model()
conn = database.connect_database()
cursor = database.create_cursor(conn)
print(cap)
detection_history=[] # mảng 2 chiều lưu tất cả loại quả xuất hiện trên 15 frame
while 1:
    frame=camera.get_frame(cap)
    if frame is None:
        break
    scale_frame=camera.crop_scale_area(frame)
    results=detector.detect(model,scale_frame)
    fruit_names=detector.get_fruit_names(results)
    detection_history=detector.update_detection_history(detection_history,fruit_names)

    if detector.has_multiple_fruit_types(detection_history):
        print('Không được có nhiều loại trái cây')
        continue

    fruit_name=detector.get_stable_fruit(detection_history)

    if fruit_name is None:
        print("Đang nhận diện trái cây")
        continue

    price = database.get_price(cursor, fruit_name)
    weight=scale.get_weight()
    total=int(price*weight)
    print("Fruit:",fruit_name)
    print("Price:", price, "đ/kg")
    print("Weight:", weight, "kg")
    print("Total:", total, "đ")
    if cv2.waitKey(1) & 0xFF ==27:
        break
conn.close()
camera.release_camera(cap)
cv2.destroyAllWindows()
