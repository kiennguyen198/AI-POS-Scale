import tkinter as tk

import cv2
from PIL import Image,ImageTk

import camera
import controller
import database
import detector
import qr
import scale
import customer_ui as ui
from config import SCALE_X1,SCALE_X2,SCALE_Y1,SCALE_Y2


UPDATE_DELAY_MS=100
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
        "cap":None,
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
        "qr_product":None,
        "last_weight_g":0,
        "camera_failures":0,
        "resources_ready":False,
        "running":True,
        "after_id":None
    }

    customer_ui=ui.create_customer_ui(
        root,
        on_create_qr=lambda:create_product_qr(app),
        on_next=lambda:start_next_weighing(app)
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
        app["cap"]=camera.open_camera()
        app["camera_failures"]=0
        return True
    except RuntimeError:
        app["cap"]=None
        ui.update_camera(app["ui"],None)
        set_customer_error(
            app,
            "Không thể mở camera. Hệ thống đang thử lại."
        )
        return False


def update_customer_app(app):
    if not app["running"] or not app["resources_ready"]:
        return

    if app["state"]==controller.SHOWING_QR:
        update_qr_waiting_screen(app)
        schedule_next_update(app,UPDATE_DELAY_MS)
        return

    if app["cap"] is None:
        camera_opened=open_customer_camera(app)
        delay=UPDATE_DELAY_MS if camera_opened else CAMERA_RETRY_MS
        schedule_next_update(app,delay)
        return

    frame=camera.get_frame(app["cap"])

    if frame is None:
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

        ui.update_product_info(app["ui"])
        ui.set_customer_state(app["ui"],app["state"])

        return draw_scale_area(frame)

    scale.update_weight_history(
        app["weight_history"],
        weight_g
    )

    scale_frame=camera.crop_scale_area(frame)

    try:
        results=detector.detect(app["model"],scale_frame)
    except Exception as error:
        app["product"]=None
        set_customer_error(
            app,
            f"Không thể nhận diện trái cây: {error}"
        )
        return draw_scale_area(frame)

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

    next_state=controller.get_qr_state(
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

    if next_state==controller.READY_TO_QR and product is None:
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

    annotated_scale_frame=results[0].plot()

    return draw_scale_area(
        frame,
        annotated_scale_frame
    )


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

    ui.set_qr_image(app["ui"],None)
    ui.update_product_info(app["ui"])
    ui.set_customer_state(app["ui"],controller.EMPTY)
    ui.show_weighing_screen(app["ui"])


def draw_scale_area(frame,annotated_scale_frame=None):
    display_frame=frame.copy()
    frame_height,frame_width=display_frame.shape[:2]

    x1=max(0,min(SCALE_X1,frame_width))
    x2=max(0,min(SCALE_X2,frame_width))
    y1=max(0,min(SCALE_Y1,frame_height))
    y2=max(0,min(SCALE_Y2,frame_height))

    if x2<=x1 or y2<=y1:
        return display_frame

    if annotated_scale_frame is not None:
        scale_width=x2-x1
        scale_height=y2-y1

        if (
            annotated_scale_frame.shape[1]!=scale_width
            or annotated_scale_frame.shape[0]!=scale_height
        ):
            annotated_scale_frame=cv2.resize(
                annotated_scale_frame,
                (scale_width,scale_height),
                interpolation=cv2.INTER_LINEAR
            )

        display_frame[
            y1:y2,
            x1:x2
        ]=annotated_scale_frame

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

    camera.release_camera(app["cap"])
    app["cap"]=None
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
    ui.set_create_qr_enabled(customer_ui,False)


def schedule_next_update(app,delay):
    if not app["running"]:
        return

    app["after_id"]=app["root"].after(
        delay,
        lambda:update_customer_app(app)
    )


def release_resources(app):
    if app["cap"] is not None:
        try:
            camera.release_camera(app["cap"])
        except Exception:
            pass
        app["cap"]=None

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
