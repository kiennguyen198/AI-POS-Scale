import tkinter as tk
import threading
import time

import cv2
from PIL import Image,ImageTk

import camera
import cart
import controller
import database
import detector
import qr
import scale
import customer_ui as ui
from config import CUSTOMER_CAMERA_SOURCE,SCALE_X1,SCALE_X2,SCALE_Y1,SCALE_Y2


UPDATE_DELAY_MS=100
DETECTION_INTERVAL_SECONDS=0.4
CAMERA_RETRY_MS=1000
MAX_CAMERA_FAILURES=10
DEFAULT_DEMO_WEIGHT_G=850

FRUIT_DISPLAY_NAMES={
    "apple":"Táo",
    "orange":"Cam",
    "banana":"Chuối",
    "mango":"Xoài",
    "guava":"Ổi"
}


def create_customer_app(
    fullscreen=False,
    use_scale=False,
    demo_weight_g=DEFAULT_DEMO_WEIGHT_G,
    calibration=None
):
    root=ui.create_window(fullscreen=fullscreen)

    app={
        "root":root,
        "ui":None,
        "camera_reader":None,
        "model":None,
        "conn":None,
        "cursor":None,
        "hx":None,
        "tare_offset":None,
        "calibration":calibration,
        "use_scale":use_scale,
        "demo_weight_g":demo_weight_g,
        "state":controller.EMPTY,
        "detection_history":[],
        "weight_history":[],
        "product":None,
        "cart":[],
        "order_id":None,
        "qr_product":None,  # kept for compatibility with the old label-QR path
        "last_weight_g":0,
        "camera_failures":0,
        "last_detection_time":0,
        "latest_detections":[],
        "detection_lock":threading.Lock(),
        "detection_running":False,
        "detection_result":None,
        "detection_error":None,
        "detection_epoch":0,
        "resources_ready":False,
        "running":True,
        "after_id":None
    }

    customer_ui=ui.create_customer_ui(
        root,
        on_add_item=lambda:add_current_product(app),
        on_payment=lambda:create_payment_qr(app),
        on_new_order=lambda:start_new_order(app),
    )
    app["ui"]=customer_ui

    root.protocol(
        "WM_DELETE_WINDOW",
        lambda:close_customer_app(app)
    )

    return app


def start_customer_app(app):
    try:
        initialize_resources(app)
    except Exception as error:
        release_resources(app)
        set_customer_error(
            app,
            f"Không thể khởi động hệ thống: {error}"
        )
        return

    schedule_next_update(app,UPDATE_DELAY_MS)


def initialize_resources(app):
    if app["use_scale"] and (
        app["calibration"] is None
        or app["calibration"]==0
    ):
        raise ValueError("chưa có hệ số calibration của cân")

    app["conn"]=database.connect_database()
    app["cursor"]=database.create_cursor(app["conn"])
    app["model"]=detector.load_model()

    if app["use_scale"]:
        app["hx"]=scale.setup_scale()

        # Khi khởi động cân thật, mặt cân phải đang trống.
        app["tare_offset"]=scale.tare_scale(app["hx"])

    app["resources_ready"]=True
    open_customer_camera(app)


def open_customer_camera(app):
    try:
        app["camera_reader"]=camera.start_latest_frame_reader(
            CUSTOMER_CAMERA_SOURCE
        )
        app["camera_failures"]=0
        return True
    except RuntimeError:
        app["camera_reader"]=None
        ui.update_camera(app["ui"],None)
        set_customer_error(
            app,
            "Không thể mở camera. Hệ thống đang thử lại."
        )
        return False


def update_customer_app(app):
    if not app["running"] or not app["resources_ready"]:
        return

    if app["state"]==controller.SHOWING_PAYMENT_QR:
        schedule_next_update(app,UPDATE_DELAY_MS)
        return

    if app["camera_reader"] is None:
        camera_opened=open_customer_camera(app)
        delay=UPDATE_DELAY_MS if camera_opened else CAMERA_RETRY_MS
        schedule_next_update(app,delay)
        return

    frame=camera.get_latest_frame(app["camera_reader"])

    if frame is None:
        if camera.is_reader_starting(app["camera_reader"]):
            schedule_next_update(app,UPDATE_DELAY_MS)
            return

        handle_camera_failure(app)
        schedule_next_update(app,UPDATE_DELAY_MS)
        return

    app["camera_failures"]=0
    weight_g=read_weight(app)

    if weight_g is None:
        display_frame=draw_scale_area(frame)
        update_camera_image(app,display_frame)
        schedule_next_update(app,UPDATE_DELAY_MS)
        return

    app["last_weight_g"]=weight_g
    display_frame=process_weighing_frame(
        app,
        frame,
        weight_g
    )
    update_camera_image(app,display_frame)

    schedule_next_update(app,UPDATE_DELAY_MS)


def process_weighing_frame(app,frame,weight_g):
    scale_empty=scale.is_scale_empty(weight_g)

    if scale_empty:
        app["detection_history"].clear()
        app["weight_history"].clear()
        app["product"]=None
        app["state"]=controller.EMPTY
        app["last_detection_time"]=0
        invalidate_detection(app)
        app["latest_detections"].clear()

        ui.update_product_info(app["ui"])
        ui.update_cart(
            app["ui"],
            app["cart"],
            cart.calculate_cart_total(app["cart"])
        )
        ui.set_customer_state(app["ui"],app["state"])

        return draw_scale_area(frame)

    if app["state"]==controller.WAITING_REMOVAL:
        # Keep the finished item in the order and wait for the customer to
        # remove it before accepting another weighing cycle.
        return draw_scale_area(frame,app["latest_detections"])

    scale.update_weight_history(
        app["weight_history"],
        weight_g
    )

    scale_frame=camera.crop_scale_area(frame)
    results,error=take_detection_result(app)

    if error is not None:
        app["product"]=None
        app["latest_detections"].clear()
        set_customer_error(
            app,
            f"Không thể nhận diện trái cây: {error}"
        )

    if results is not None:
        process_detection_result(app,results,weight_g,scale_empty)

    detection_elapsed=time.monotonic()-app["last_detection_time"]
    if (
        detection_elapsed>=DETECTION_INTERVAL_SECONDS
        and not is_detection_running(app)
    ):
        start_detection(app,scale_frame)

    return draw_scale_area(
        frame,
        app["latest_detections"]
    )


def start_detection(app,scale_frame):
    with app["detection_lock"]:
        if app["detection_running"]:
            return

        app["detection_running"]=True
        app["detection_result"]=None
        app["detection_error"]=None
        detection_epoch=app["detection_epoch"]
        app["last_detection_time"]=time.monotonic()

    detection_thread=threading.Thread(
        target=run_detection,
        args=(app,scale_frame.copy(),detection_epoch),
        daemon=True
    )
    detection_thread.start()


def run_detection(app,scale_frame,detection_epoch):
    try:
        results=detector.detect(app["model"],scale_frame)
        error=None
    except Exception as detection_error:
        results=None
        error=detection_error

    with app["detection_lock"]:
        if detection_epoch==app["detection_epoch"]:
            app["detection_result"]=results
            app["detection_error"]=error

        app["detection_running"]=False


def is_detection_running(app):
    with app["detection_lock"]:
        return app["detection_running"]


def take_detection_result(app):
    with app["detection_lock"]:
        results=app["detection_result"]
        error=app["detection_error"]
        app["detection_result"]=None
        app["detection_error"]=None

    return results,error


def invalidate_detection(app):
    with app["detection_lock"]:
        app["detection_epoch"]+=1
        app["detection_result"]=None
        app["detection_error"]=None


def process_detection_result(app,results,weight_g,scale_empty):
    if scale_empty:
        return

    fruit_names=detector.get_fruit_names(results)
    detector.update_detection_history(
        app["detection_history"],
        fruit_names
    )

    mixed_fruits=detector.has_multiple_fruit_types(
        app["detection_history"]
    )
    stable_fruit=detector.get_stable_fruit(
        app["detection_history"]
    )
    weight_stable=scale.is_weight_stable(
        app["weight_history"]
    )

    next_state=controller.get_weighing_state(
        app["state"],
        scale_empty,
        mixed_fruits,
        stable_fruit,
        weight_stable
    )

    product,price_missing=build_product(
        app,
        stable_fruit,
        weight_g,
        mixed_fruits
    )

    if next_state==controller.READY_TO_ADD and product is None:
        next_state=controller.DETECTING

    app["product"]=product
    app["state"]=next_state

    update_weighing_information(
        app,
        stable_fruit,
        weight_g,
        product
    )
    ui.set_customer_state(app["ui"],app["state"])

    if weight_g<0:
        app["product"]=None
        set_customer_error(
            app,
            "Khối lượng đang âm. Hãy kiểm tra lại tare và calibration."
        )
    elif price_missing:
        set_customer_error(
            app,
            f"Không tìm thấy giá của {stable_fruit} trong database."
        )

    result=results[0]
    translated_names={}

    for class_id,class_name in result.names.items():
        translated_names[class_id]=FRUIT_DISPLAY_NAMES.get(
            class_name,
            class_name
        )

    result.names=translated_names
    app["latest_detections"]=extract_detections(result)


def extract_detections(result):
    detections=[]
    boxes=result.boxes

    if boxes is None or len(boxes)==0:
        return detections

    coordinates=boxes.xyxy.cpu().numpy()
    class_ids=boxes.cls.cpu().numpy().astype(int)
    confidences=boxes.conf.cpu().numpy()

    for box,class_id,confidence in zip(
        coordinates,
        class_ids,
        confidences
    ):
        detections.append(
            (
                float(box[0]),
                float(box[1]),
                float(box[2]),
                float(box[3]),
                result.names[int(class_id)],
                float(confidence)
            )
        )

    return detections


def read_weight(app):
    if not app["use_scale"]:
        return round(app["demo_weight_g"])

    try:
        return scale.get_weight(
            app["hx"],
            app["tare_offset"],
            app["calibration"]
        )
    except Exception as error:
        app["product"]=None
        set_customer_error(
            app,
            f"Không thể đọc khối lượng: {error}"
        )
        return None


def build_product(
    app,
    stable_fruit,
    weight_g,
    mixed_fruits
):
    if stable_fruit is None or mixed_fruits or weight_g<=0:
        return None,False

    try:
        price_per_kg=database.get_price(
            app["cursor"],
            stable_fruit
        )
    except Exception as error:
        set_customer_error(
            app,
            f"Không thể đọc database: {error}"
        )
        return None,True

    if price_per_kg is None or price_per_kg<=0:
        return None,True

    display_name=FRUIT_DISPLAY_NAMES.get(
        stable_fruit,
        stable_fruit.capitalize()
    )
    total=round(price_per_kg*weight_g/1000)

    product={
        "model_class":stable_fruit,
        "display_name":display_name,
        "weight_g":weight_g,
        "price_per_kg":price_per_kg,
        "total":total
    }

    return product,False


def update_weighing_information(
    app,
    stable_fruit,
    weight_g,
    product
):
    if product is not None:
        ui.update_product_info(
            app["ui"],
            product["display_name"],
            product["weight_g"],
            product["price_per_kg"],
            product["total"]
        )
        return

    display_name=None

    if stable_fruit is not None:
        display_name=FRUIT_DISPLAY_NAMES.get(
            stable_fruit,
            stable_fruit.capitalize()
        )

    ui.update_product_info(
        app["ui"],
        display_name,
        weight_g,
        0,
        0
    )


def create_product_qr(app):
    if (
        app["state"]!=controller.READY_TO_QR
        or app["product"] is None
    ):
        return

    product=app["product"].copy()

    if app["use_scale"]:
        current_weight=read_weight(app)

        if current_weight is None:
            return

        app["last_weight_g"]=current_weight
        scale.update_weight_history(
            app["weight_history"],
            current_weight
        )

        if scale.is_scale_empty(current_weight):
            app["state"]=controller.EMPTY
            app["product"]=None
            ui.update_product_info(app["ui"])
            ui.set_customer_state(app["ui"],app["state"])
            return

        if not scale.is_weight_stable(app["weight_history"]):
            app["state"]=controller.STABILIZING
            ui.set_customer_state(app["ui"],app["state"])
            return

        product["weight_g"]=current_weight
        product["total"]=round(
            product["price_per_kg"]*current_weight/1000
        )

    try:
        label_id=qr.create_label_id()
        qr_data=qr.create_qr_data(
            label_id,
            product["model_class"],
            product["weight_g"],
            product["price_per_kg"]
        )
        qr_image=qr.create_qr_image(qr_data)
    except Exception as error:
        set_customer_error(
            app,
            f"Không thể tạo QR: {error}"
        )
        return

    product["label_id"]=label_id
    product["qr_data"]=qr_data
    app["qr_product"]=product
    app["state"]=controller.show_qr(app["state"])

    ui.show_qr_screen(
        app["ui"],
        qr_image,
        product["display_name"],
        product["weight_g"],
        product["price_per_kg"],
        product["total"],
        can_continue=not app["use_scale"]
    )


def update_qr_waiting_screen(app):
    if not app["use_scale"]:
        ui.set_next_enabled(app["ui"],True)
        return

    weight_g=read_weight(app)

    if weight_g is None:
        ui.set_next_enabled(app["ui"],False)
        return

    app["last_weight_g"]=weight_g
    scale_empty=scale.is_scale_empty(weight_g)
    ui.set_next_enabled(app["ui"],scale_empty)


def start_next_weighing(app):
    scale_empty=(
        True
        if not app["use_scale"]
        else scale.is_scale_empty(app["last_weight_g"])
    )
    next_state=controller.next_weighing(
        app["state"],
        scale_empty
    )

    if next_state!=controller.EMPTY:
        ui.set_next_enabled(app["ui"],False)
        return

    reset_weighing_cycle(app)


def reset_weighing_cycle(app):
    app["state"]=controller.EMPTY
    app["detection_history"].clear()
    app["weight_history"].clear()
    app["product"]=None
    app["qr_product"]=None
    app["last_weight_g"]=0
    app["last_detection_time"]=0
    invalidate_detection(app)
    app["latest_detections"].clear()

    ui.set_qr_image(app["ui"],None)
    ui.update_product_info(app["ui"])
    ui.set_customer_state(app["ui"],controller.EMPTY)
    ui.show_weighing_screen(app["ui"])


def _reset_current_item(app, state):
    """Clear only the item on the platform, preserving the current cart."""
    app["product"] = None
    app["detection_history"].clear()
    app["weight_history"].clear()
    app["last_weight_g"] = 0
    app["last_detection_time"] = 0
    app["latest_detections"].clear()
    invalidate_detection(app)
    app["state"] = state
    ui.update_product_info(app["ui"])
    ui.update_cart(
        app["ui"],
        app["cart"],
        cart.calculate_cart_total(app["cart"]),
    )
    ui.set_customer_state(app["ui"], state)


def add_current_product(app):
    """Commit the stable item on the platform as one cart line."""
    if app["state"] != controller.READY_TO_ADD or app["product"] is None:
        return

    product = app["product"].copy()
    if app["use_scale"]:
        current_weight = read_weight(app)
        if current_weight is None or scale.is_scale_empty(current_weight):
            _reset_current_item(app, controller.EMPTY)
            return

        app["last_weight_g"] = current_weight
        scale.update_weight_history(app["weight_history"], current_weight)
        if not scale.is_weight_stable(app["weight_history"]):
            app["state"] = controller.STABILIZING
            ui.set_customer_state(app["ui"], app["state"])
            return

        product["weight_g"] = current_weight
        product["total"] = round(
            product["price_per_kg"] * current_weight / 1000
        )

    cart.add_item(
        app["cart"],
        product["display_name"],
        product["weight_g"],
        product["price_per_kg"],
    )
    ui.update_cart(
        app["ui"],
        app["cart"],
        cart.calculate_cart_total(app["cart"]),
    )

    if app["use_scale"]:
        # A real scale must return to zero before the next line can be added.
        _reset_current_item(app, controller.WAITING_REMOVAL)
    else:
        # Demo mode has no empty-platform signal, so allow another demo cycle.
        _reset_current_item(app, controller.EMPTY)


def create_payment_qr(app):
    """Show one QR containing the order reference and total cart amount."""
    if not app["cart"] or app["state"] != controller.EMPTY:
        return

    total = cart.calculate_cart_total(app["cart"])
    order_id = qr.create_order_id()
    qr_data = qr.create_payment_qr_data(order_id, total)

    try:
        qr_image = qr.create_qr_image(qr_data)
    except Exception as error:
        set_customer_error(app, f"Không thể tạo QR thanh toán: {error}")
        return

    app["order_id"] = order_id
    app["state"] = controller.SHOWING_PAYMENT_QR
    ui.show_payment_qr(
        app["ui"],
        qr_image,
        order_id,
        total,
        len(app["cart"]),
    )


def start_new_order(app):
    """Clear the paid/demo order and return to the weighing screen."""
    app["cart"].clear()
    app["order_id"] = None
    _reset_current_item(app, controller.EMPTY)
    ui.show_weighing_screen(app["ui"])


# Public compatibility aliases for scripts that used the previous button names.
create_product_qr = create_payment_qr
start_next_weighing = start_new_order


def draw_scale_area(frame,detections=None):
    display_frame=frame.copy()
    frame_height,frame_width=display_frame.shape[:2]

    x1=max(0,min(SCALE_X1,frame_width))
    x2=max(0,min(SCALE_X2,frame_width))
    y1=max(0,min(SCALE_Y1,frame_height))
    y2=max(0,min(SCALE_Y2,frame_height))

    if x2<=x1 or y2<=y1:
        return display_frame

    if detections:
        current_scale_frame=display_frame[y1:y2,x1:x2]
        scale_height,scale_width=current_scale_frame.shape[:2]

        for (
            box_x1,
            box_y1,
            box_x2,
            box_y2,
            class_name,
            confidence
        ) in detections:
            box_x1=max(0,min(round(box_x1),scale_width-1))
            box_y1=max(0,min(round(box_y1),scale_height-1))
            box_x2=max(0,min(round(box_x2),scale_width-1))
            box_y2=max(0,min(round(box_y2),scale_height-1))

            cv2.rectangle(
                current_scale_frame,
                (box_x1,box_y1),
                (box_x2,box_y2),
                (40,180,255),
                2
            )

            label=f"{class_name} {confidence:.2f}"
            label_y=max(18,box_y1-6)
            cv2.putText(
                current_scale_frame,
                label,
                (box_x1,label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (40,180,255),
                1,
                cv2.LINE_AA
            )

    cv2.rectangle(
        display_frame,
        (x1,y1),
        (x2-1,y2-1),
        (255,180,40),
        2
    )

    return display_frame


def update_camera_image(app,frame):
    photo_image=frame_to_photo(
        frame,
        app["ui"]["camera_canvas"]
    )
    ui.update_camera(app["ui"],photo_image)


def frame_to_photo(frame,canvas):
    canvas_width=canvas.winfo_width()
    canvas_height=canvas.winfo_height()

    if canvas_width<=1 or canvas_height<=1:
        canvas_width=640
        canvas_height=480

    frame_height,frame_width=frame.shape[:2]
    width_scale=canvas_width/frame_width
    height_scale=canvas_height/frame_height
    resize_scale=min(width_scale,height_scale)

    display_width=max(1,round(frame_width*resize_scale))
    display_height=max(1,round(frame_height*resize_scale))

    if display_width!=frame_width or display_height!=frame_height:
        interpolation=(
            cv2.INTER_AREA
            if resize_scale<1
            else cv2.INTER_LINEAR
        )
        frame=cv2.resize(
            frame,
            (display_width,display_height),
            interpolation=interpolation
        )

    rgb_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    image=Image.fromarray(rgb_frame)

    return ImageTk.PhotoImage(image)


def handle_camera_failure(app):
    app["camera_failures"]+=1
    app["product"]=None
    app["state"]=controller.DETECTING

    if app["camera_failures"]==1:
        set_customer_error(
            app,
            "Không đọc được hình ảnh từ camera."
        )

    if app["camera_failures"]<MAX_CAMERA_FAILURES:
        return

    camera.stop_latest_frame_reader(app["camera_reader"])
    app["camera_reader"]=None
    app["camera_failures"]=0
    ui.update_camera(app["ui"],None)
    set_customer_error(
        app,
        "Mất kết nối camera. Hệ thống đang thử lại."
    )


def set_customer_error(app,message):
    customer_ui=app["ui"]
    customer_ui["header_status"].configure(
        text="Lỗi hệ thống",
        fg="#C2413A",
        bg="#FDE8E7"
    )
    customer_ui["instruction_var"].set(message)
    customer_ui["add_item_button"].configure(state=tk.DISABLED)
    customer_ui["payment_button"].configure(state=tk.DISABLED)


def schedule_next_update(app,delay):
    if not app["running"]:
        return

    app["after_id"]=app["root"].after(
        delay,
        lambda:update_customer_app(app)
    )


def release_resources(app):
    if app["camera_reader"] is not None:
        try:
            camera.stop_latest_frame_reader(app["camera_reader"])
        except Exception:
            pass
        app["camera_reader"]=None

    if app["conn"] is not None:
        try:
            app["conn"].close()
        except Exception:
            pass
        app["conn"]=None
        app["cursor"]=None

    if app["hx"] is not None:
        try:
            scale.cleanup_scale()
        except Exception:
            pass
        app["hx"]=None

    app["model"]=None
    app["resources_ready"]=False


def close_customer_app(app):
    app["running"]=False

    if app["after_id"] is not None:
        try:
            app["root"].after_cancel(app["after_id"])
        except tk.TclError:
            pass

    release_resources(app)

    try:
        app["root"].destroy()
    except tk.TclError:
        pass


def run(
    fullscreen=False,
    use_scale=False,
    demo_weight_g=DEFAULT_DEMO_WEIGHT_G,
    calibration=None
):
    app=create_customer_app(
        fullscreen=fullscreen,
        use_scale=use_scale,
        demo_weight_g=demo_weight_g,
        calibration=calibration
    )
    app["after_id"]=app["root"].after(
        100,
        lambda:start_customer_app(app)
    )
    app["root"].mainloop()


if __name__=="__main__":
    run()
