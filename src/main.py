# mọi thứ gặp nhau ở main, main điều phối, và các module không được biết nhau
# tên biến luôn viết in hoa để mọi người hiểu đây là hằng số cấu hình 
# nhớ chia theo module
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
while 1:
    frame=camera.get_frame(cap)
    if frame is None:
        break
    results=detector.detect(model,frame)
    fruit_names=detector.get_fruit_names(results)
    if not detector.has_fruit(fruit_names):
        print('Chưa có trái cây')
        continue
    if not detector.check_single_fruit_type(fruit_names):
        print("Không được có nhiều loại trái cây")
        continue
    fruit_name = fruit_names[0]
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
