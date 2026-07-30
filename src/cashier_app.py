import tkinter as tk

import cv2
from PIL import Image, ImageTk

import camera
import cart
import cashier_ui
import scanner
from config import CASHIER_CAMERA_SOURCE


FRAME_DELAY_MS=30
CAMERA_RETRY_MS=1000
MAX_CAMERA_FAILURES=10

FRUIT_DISPLAY_NAMES={
    "apple":"Táo",
    "orange":"Cam",
    "banana":"Chuối",
    "mango":"Xoài",
    "guava":"Ổi"
}


def create_cashier_app():
    root=cashier_ui.create_window()

    app={
        "root":root,
        "ui":None,
        "cap":None,
        "cart":[],
        "scan_locked":False,
        "no_qr_frames":0,
        "qr_visible":False,
        "camera_failures":0,
        "running":True,
        "after_id":None
    }

    ui=cashier_ui.create_cashier_ui(
        root,
        on_remove=lambda item_index:remove_product(app,item_index),
        on_clear=lambda:clear_invoice(app),
        on_complete=lambda:complete_invoice(app)
    )
    app["ui"]=ui

    root.protocol(
        "WM_DELETE_WINDOW",
        lambda:close_app(app)
    )

    return app


def open_camera(app):
    try:
        app["cap"]=camera.open_camera(CASHIER_CAMERA_SOURCE)
        app["camera_failures"]=0
        cashier_ui.set_scan_status(
            app["ui"],
            "Sẵn sàng quét",
            "ready"
        )
        return True

    except RuntimeError:
        app["cap"]=None
        cashier_ui.update_camera(app["ui"],None)
        cashier_ui.set_scan_status(
            app["ui"],
            "Không thể mở webcam",
            "error"
        )
        return False


def update_frame(app):
    if not app["running"]:
        return

    if app["cap"] is None:
        camera_opened=open_camera(app)
        delay=FRAME_DELAY_MS if camera_opened else CAMERA_RETRY_MS
        schedule_next_frame(app,delay)
        return

    frame=camera.get_frame(app["cap"])

    if frame is None:
        handle_camera_failure(app)
        schedule_next_frame(app,FRAME_DELAY_MS)
        return

    app["camera_failures"]=0
    product,qr_points=scanner.scan_frame(frame)

    was_locked=app["scan_locked"]
    was_visible=app["qr_visible"]

    should_add,scan_locked,no_qr_frames=scanner.update_scan_state(
        product,
        qr_points,
        app["scan_locked"],
        app["no_qr_frames"]
    )

    app["scan_locked"]=scan_locked
    app["no_qr_frames"]=no_qr_frames
    app["qr_visible"]=qr_points is not None

    update_cart_from_scan(
        app,
        product,
        qr_points,
        should_add,
        was_locked,
        was_visible
    )

    draw_qr_box(frame,qr_points,product)
    photo_image=frame_to_photo(
        frame,
        app["ui"]["camera_canvas"]
    )
    cashier_ui.update_camera(app["ui"],photo_image)

    schedule_next_frame(app,FRAME_DELAY_MS)


def update_cart_from_scan(
    app,
    product,
    qr_points,
    should_add,
    was_locked,
    was_visible
):
    if should_add:
        product["fruit_name"]=FRUIT_DISPLAY_NAMES.get(
            product["fruit_name"],
            product["fruit_name"]
        )

        product_added=cart.add_scanned_product(
            app["cart"],
            product,
            should_add
        )

        if not product_added:
            cashier_ui.set_scan_status(
                app["ui"],
                "QR này đã có trong hóa đơn - đưa QR ra khỏi camera",
                "warning"
            )
            return

        cashier_ui.set_cart(app["ui"],app["cart"])
        cashier_ui.set_scan_status(
            app["ui"],
            f'Đã thêm {product["fruit_name"]} - đưa QR ra khỏi camera',
            "success"
        )
        return

    if (
        qr_points is not None
        and product is None
        and not app["scan_locked"]
    ):
        cashier_ui.set_scan_status(
            app["ui"],
            "QR không hợp lệ",
            "error"
        )
        return

    scanner_unlocked=was_locked and not app["scan_locked"]
    qr_removed=was_visible and not app["qr_visible"]

    if scanner_unlocked or (qr_removed and not app["scan_locked"]):
        cashier_ui.set_scan_status(
            app["ui"],
            "Sẵn sàng quét",
            "ready"
        )


def handle_camera_failure(app):
    app["camera_failures"]+=1

    if app["camera_failures"]<MAX_CAMERA_FAILURES:
        return

    camera.release_camera(app["cap"])
    app["cap"]=None
    app["camera_failures"]=0
    cashier_ui.update_camera(app["ui"],None)
    cashier_ui.set_scan_status(
        app["ui"],
        "Mất kết nối webcam - đang thử lại",
        "error"
    )


def draw_qr_box(frame,qr_points,product):
    if qr_points is None or product is None:
        return

    points=qr_points.astype("int32").reshape(-1,2)

    if points.shape!=(4,2):
        return

    if not cv2.isContourConvex(points):
        return

    if cv2.contourArea(points)<500:
        return

    cv2.polylines(
        frame,
        [points],
        True,
        (255,180,40),
        3
    )


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
    photo_image=ImageTk.PhotoImage(image)

    return photo_image


def remove_product(app,item_index):
    if item_index<0 or item_index>=len(app["cart"]):
        return

    removed_item=cart.remove_item(app["cart"],item_index)
    cashier_ui.set_cart(app["ui"],app["cart"])
    cashier_ui.set_scan_status(
        app["ui"],
        f'Đã xóa {removed_item["fruit_name"]}',
        "warning"
    )


def clear_invoice(app):
    cart.clear_cart(app["cart"])
    cashier_ui.set_cart(app["ui"],app["cart"])
    cashier_ui.set_scan_status(
        app["ui"],
        "Hóa đơn đã được hủy",
        "warning"
    )


def complete_invoice(app):
    cart.clear_cart(app["cart"])
    cashier_ui.set_cart(app["ui"],app["cart"])
    cashier_ui.set_scan_status(
        app["ui"],
        "Hóa đơn đã hoàn tất",
        "success"
    )


def schedule_next_frame(app,delay):
    if not app["running"]:
        return

    app["after_id"]=app["root"].after(
        delay,
        lambda:update_frame(app)
    )


def close_app(app):
    app["running"]=False

    if app["after_id"] is not None:
        try:
            app["root"].after_cancel(app["after_id"])
        except tk.TclError:
            pass

    if app["cap"] is not None:
        camera.release_camera(app["cap"])
        app["cap"]=None

    app["root"].destroy()


def run():
    app=create_cashier_app()
    open_camera(app)
    schedule_next_frame(app,100)
    app["root"].mainloop()


if __name__=="__main__":
    run()
