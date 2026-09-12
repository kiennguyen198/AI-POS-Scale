"""Tkinter customer screen for the AI POS Scale self-checkout kiosk."""

import ctypes
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk

from config import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    SCALE_X1,
    SCALE_X2,
    SCALE_Y1,
    SCALE_Y2,
)


BG_COLOR = "#F3F7FF"
CARD_COLOR = "#FFFFFF"
TEXT_COLOR = "#12335B"
MUTED_COLOR = "#64748B"
PRIMARY_COLOR = "#2F6BFF"
PRIMARY_DARK = "#1647B8"
BORDER_COLOR = "#D7E3F4"
DANGER_COLOR = "#C2413A"
CAMERA_COLOR = "#0A1E38"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UIT_LOGO_PATH = PROJECT_ROOT / "images" / "uit_logo_vietnamese.png"


STATE_STYLES = {
    "EMPTY": (
        "Cân đang trống",
        "#5F6B67",
        "#E8EEEB",
        "Đặt một túi trái cây cùng loại lên vùng cân.",
    ),
    "DETECTING": (
        "Đang nhận diện",
        "#986319",
        "#FFF3D7",
        "Giữ túi đứng yên để hệ thống xác định loại trái cây.",
    ),
    "MIXED_BLOCKED": (
        "Nhiều loại trái cây",
        DANGER_COLOR,
        "#FDE8E7",
        "Mỗi lần cân chỉ xử lý một loại trái cây.",
    ),
    "STABILIZING": (
        "Đang ổn định",
        "#24649A",
        "#E4F1FB",
        "Không chạm vào túi trong lúc hệ thống chốt khối lượng.",
    ),
    "READY_TO_ADD": (
        "Sẵn sàng thêm món",
        PRIMARY_COLOR,
        "#E5EEFF",
        "Thông tin đã ổn định. Bấm thêm món vào hóa đơn.",
    ),
    "WAITING_REMOVAL": (
        "Đã thêm vào hóa đơn",
        PRIMARY_COLOR,
        "#E5EEFF",
        "Lấy túi khỏi cân để tiếp tục thêm loại trái cây khác.",
    ),
    "SHOWING_PAYMENT_QR": (
        "Hiển thị QR thanh toán",
        PRIMARY_COLOR,
        "#E5EEFF",
        "QR tổng hóa đơn đã sẵn sàng. Xác nhận giao dịch sẽ tích hợp sau.",
    ),
}


def format_money(value):
    return f"{int(value):,}".replace(",", ".") + " đ"


def _enable_dpi_awareness():
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def create_window(fullscreen=False):
    _enable_dpi_awareness()
    root = tk.Tk()
    screen_dpi = root.winfo_fpixels("1i")
    root.tk.call("tk", "scaling", screen_dpi / 72)
    root.title("AI POS Scale - Màn hình khách hàng")
    root.geometry("1100x700")
    root.minsize(900, 560)
    root.configure(bg=BG_COLOR)

    if fullscreen:
        root.attributes("-fullscreen", True)

    root.bind("<Escape>", lambda event: root.attributes("-fullscreen", False))
    return root


def _create_brand_header(header, ui, subtitle):
    brand_frame = tk.Frame(header, bg=CARD_COLOR)
    brand_frame.place(x=24, rely=0.5, anchor="w")

    if UIT_LOGO_PATH.exists():
        logo_image = Image.open(UIT_LOGO_PATH)
        logo_size = (150, 54) if ui["compact"] else (180, 65)
        logo_image.thumbnail(logo_size, Image.Resampling.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_image)
        ui["ui_logo_photo"] = logo_photo
        tk.Label(brand_frame, image=logo_photo, bg=CARD_COLOR, bd=0).pack(side="left")
    else:
        tk.Label(
            brand_frame,
            text="UIT",
            font=("Segoe UI", 22, "bold"),
            fg=PRIMARY_COLOR,
            bg=CARD_COLOR,
        ).pack(side="left")

    product_frame = tk.Frame(header, bg=CARD_COLOR)
    product_frame.place(relx=0.5, rely=0.5, anchor="center")
    tk.Label(
        product_frame,
        text="AI POS SCALE",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).pack(anchor="w")
    tk.Label(
        product_frame,
        text=subtitle,
        font=("Segoe UI", 9),
        fg=MUTED_COLOR,
        bg=CARD_COLOR,
    ).pack(anchor="w")


def create_customer_ui(
    root,
    on_add_item=None,
    on_payment=None,
    on_new_order=None,
    # Compatibility names for the previous product-label prototype.
    on_create_qr=None,
    on_next=None,
):
    if on_add_item is None:
        on_add_item = on_create_qr
    if on_new_order is None:
        on_new_order = on_next

    ui = {}
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    ui["compact"] = screen_width <= 1100 or screen_height <= 700
    ui["qr_size"] = 260 if ui["compact"] else 330
    ui["cart_count"] = 0

    header_height = 72 if ui["compact"] else 82
    content_pad = 14 if ui["compact"] else 24
    content_gap = 12 if ui["compact"] else 22

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)

    header = tk.Frame(
        root,
        bg=CARD_COLOR,
        height=header_height,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
    )
    header.grid(row=0, column=0, sticky="ew")
    header.grid_propagate(False)
    _create_brand_header(header, ui, "Cân trái cây tự phục vụ")

    ui["header_status"] = tk.Label(
        header,
        text="Cân đang trống",
        font=("Segoe UI", 11, "bold"),
        fg="#5F6B67",
        bg="#E8EEEB",
        padx=18,
        pady=9,
    )
    ui["header_status"].place(
        relx=1.0,
        x=-content_pad,
        rely=0.5,
        anchor="e",
    )

    content = tk.Frame(root, bg=BG_COLOR)
    content.grid(row=1, column=0, padx=content_pad, pady=content_gap, sticky="nsew")
    content.grid_rowconfigure(0, weight=1)
    content.grid_columnconfigure(0, weight=1)

    weighing_screen = tk.Frame(content, bg=BG_COLOR)
    weighing_screen.grid(row=0, column=0, sticky="nsew")
    weighing_screen.grid_rowconfigure(0, weight=1)
    weighing_screen.grid_columnconfigure(0, weight=3)
    weighing_screen.grid_columnconfigure(1, weight=2)

    payment_screen = tk.Frame(content, bg=BG_COLOR)
    payment_screen.grid(row=0, column=0, sticky="nsew")
    payment_screen.grid_rowconfigure(0, weight=1)
    payment_screen.grid_columnconfigure(0, weight=3)
    payment_screen.grid_columnconfigure(1, weight=2)

    ui["weighing_screen"] = weighing_screen
    ui["payment_screen"] = payment_screen

    _create_weighing_screen(ui, on_add_item, on_payment)
    _create_payment_screen(ui, on_new_order)

    show_weighing_screen(ui)
    set_customer_state(ui, "EMPTY")
    return ui


def _create_weighing_screen(ui, on_add_item, on_payment):
    screen = ui["weighing_screen"]

    camera_card = tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
    )
    camera_card.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
    camera_card.grid_rowconfigure(1, weight=1)
    camera_card.grid_columnconfigure(0, weight=1)

    camera_header = tk.Frame(camera_card, bg=CARD_COLOR)
    camera_header.grid(row=0, column=0, padx=20, pady=(16, 12), sticky="ew")
    tk.Label(
        camera_header,
        text="CAMERA TRỰC TIẾP",
        font=("Segoe UI", 12, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).pack(side="left")
    tk.Label(
        camera_header,
        text="Vùng mặt cân",
        font=("Segoe UI", 9, "bold"),
        fg=PRIMARY_COLOR,
        bg="#E7EFFF",
        padx=10,
        pady=5,
    ).pack(side="right")

    camera_canvas = tk.Canvas(camera_card, bg=CAMERA_COLOR, highlightthickness=0)
    camera_canvas.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="nsew")
    ui["camera_canvas"] = camera_canvas
    ui["camera_image_id"] = camera_canvas.create_image(0, 0, anchor="center")
    ui["camera_photo"] = None
    camera_canvas.bind("<Configure>", lambda event: _draw_camera_placeholder(ui, event))

    info_card = tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
    )
    info_card.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
    info_card.grid_columnconfigure(0, weight=1)

    tk.Label(
        info_card,
        text="MÓN ĐANG CÂN",
        font=("Segoe UI", 12, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).grid(row=0, column=0, padx=24, pady=(18, 12), sticky="w")

    ui["fruit_var"] = tk.StringVar(value="Chưa xác định")
    ui["weight_var"] = tk.StringVar(value="0 g")
    ui["price_var"] = tk.StringVar(value="0 đ/kg")
    ui["total_var"] = tk.StringVar(value="0 đ")
    ui["instruction_var"] = tk.StringVar()
    _create_info_row(info_card, 1, "Loại trái cây", ui["fruit_var"])
    _create_info_row(info_card, 2, "Khối lượng", ui["weight_var"])
    _create_info_row(info_card, 3, "Đơn giá", ui["price_var"])

    total_frame = tk.Frame(info_card, bg="#EAF1FF")
    total_frame.grid(row=4, column=0, padx=24, pady=(12, 8), sticky="ew")
    tk.Label(
        total_frame,
        text="THÀNH TIỀN MÓN NÀY",
        font=("Segoe UI", 9, "bold"),
        fg=MUTED_COLOR,
        bg="#EAF1FF",
    ).pack(anchor="w", padx=16, pady=(10, 1))
    tk.Label(
        total_frame,
        textvariable=ui["total_var"],
        font=("Segoe UI", 21, "bold"),
        fg=PRIMARY_DARK,
        bg="#EAF1FF",
    ).pack(anchor="w", padx=16, pady=(0, 10))

    instruction = tk.Label(
        info_card,
        textvariable=ui["instruction_var"],
        font=("Segoe UI", 9),
        fg=MUTED_COLOR,
        bg=CARD_COLOR,
        justify="left",
        wraplength=330,
    )
    instruction.grid(row=5, column=0, padx=24, pady=(2, 8), sticky="w")

    tk.Label(
        info_card,
        text="HÓA ĐƠN HIỆN TẠI",
        font=("Segoe UI", 10, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).grid(row=6, column=0, padx=24, pady=(4, 4), sticky="w")

    ui["cart_listbox"] = tk.Listbox(
        info_card,
        height=4,
        font=("Segoe UI", 9),
        activestyle="none",
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
        bg="#FAFCFF",
        fg=TEXT_COLOR,
        selectbackground="#FAFCFF",
        selectforeground=TEXT_COLOR,
    )
    ui["cart_listbox"].grid(row=7, column=0, padx=24, pady=(0, 5), sticky="ew")

    ui["cart_total_var"] = tk.StringVar(value="Tổng hóa đơn: 0 đ")
    tk.Label(
        info_card,
        textvariable=ui["cart_total_var"],
        font=("Segoe UI", 12, "bold"),
        fg=PRIMARY_DARK,
        bg=CARD_COLOR,
    ).grid(row=8, column=0, padx=24, pady=(2, 8), sticky="e")

    button_frame = tk.Frame(info_card, bg=CARD_COLOR)
    button_frame.grid(row=9, column=0, padx=24, pady=(0, 18), sticky="ew")
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)

    ui["add_item_button"] = tk.Button(
        button_frame,
        text="THÊM VÀO HÓA ĐƠN",
        command=on_add_item if on_add_item is not None else lambda: None,
        font=("Segoe UI", 10, "bold"),
        fg="white",
        bg=PRIMARY_COLOR,
        activeforeground="white",
        activebackground=PRIMARY_DARK,
        disabledforeground="#A8B2AE",
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=10,
    )
    ui["add_item_button"].grid(row=0, column=0, padx=(0, 5), sticky="ew")

    ui["payment_button"] = tk.Button(
        button_frame,
        text="THANH TOÁN / HIỆN QR",
        command=on_payment if on_payment is not None else lambda: None,
        font=("Segoe UI", 10, "bold"),
        fg="white",
        bg="#15966D",
        activeforeground="white",
        activebackground="#0D7655",
        disabledforeground="#A8B2AE",
        relief="flat",
        cursor="hand2",
        padx=10,
        pady=10,
    )
    ui["payment_button"].grid(row=0, column=1, padx=(5, 0), sticky="ew")

def _create_payment_screen(ui, on_new_order):
    screen = ui["payment_screen"]

    qr_card = tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
    )
    qr_card.grid(row=0, column=0, padx=(0, 12), sticky="nsew")
    qr_card.grid_rowconfigure(1, weight=1)
    qr_card.grid_columnconfigure(0, weight=1)

    tk.Label(
        qr_card,
        text="QUÉT QR ĐỂ THANH TOÁN",
        font=("Segoe UI", 15, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).grid(row=0, column=0, pady=(22, 8))
    ui["qr_image_label"] = tk.Label(
        qr_card,
        text="QR",
        font=("Segoe UI", 36, "bold"),
        fg=MUTED_COLOR,
        bg="white",
        width=11,
        height=6,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
    )
    ui["qr_image_label"].grid(row=1, column=0, padx=28, pady=14)
    ui["qr_photo"] = None
    ui["payment_hint_var"] = tk.StringVar(
        value="QR prototype chứa mã đơn và số tiền; chưa kết nối ngân hàng thật."
    )
    tk.Label(
        qr_card,
        textvariable=ui["payment_hint_var"],
        font=("Segoe UI", 10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR,
        wraplength=480,
        justify="center",
    ).grid(row=2, column=0, pady=(0, 22))

    summary_card = tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR,
    )
    summary_card.grid(row=0, column=1, padx=(12, 0), sticky="nsew")
    summary_card.grid_columnconfigure(0, weight=1)
    tk.Label(
        summary_card,
        text="TỔNG HÓA ĐƠN",
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).grid(row=0, column=0, padx=24, pady=(24, 16), sticky="w")

    ui["order_id_var"] = tk.StringVar(value="Mã đơn: -")
    ui["payment_items_var"] = tk.StringVar(value="Số món: 0")
    ui["payment_total_var"] = tk.StringVar(value="0 đ")
    tk.Label(
        summary_card,
        textvariable=ui["order_id_var"],
        font=("Segoe UI", 10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR,
    ).grid(row=1, column=0, padx=24, pady=5, sticky="w")
    tk.Label(
        summary_card,
        textvariable=ui["payment_items_var"],
        font=("Segoe UI", 11, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).grid(row=2, column=0, padx=24, pady=5, sticky="w")
    total_frame = tk.Frame(summary_card, bg="#EAF1FF")
    total_frame.grid(row=3, column=0, padx=24, pady=(18, 14), sticky="ew")
    tk.Label(
        total_frame,
        text="SỐ TIỀN CẦN THANH TOÁN",
        font=("Segoe UI", 10, "bold"),
        fg=MUTED_COLOR,
        bg="#EAF1FF",
    ).pack(anchor="w", padx=18, pady=(14, 2))
    tk.Label(
        total_frame,
        textvariable=ui["payment_total_var"],
        font=("Segoe UI", 25, "bold"),
        fg=PRIMARY_DARK,
        bg="#EAF1FF",
    ).pack(anchor="w", padx=18, pady=(0, 14))

    ui["new_order_button"] = tk.Button(
        summary_card,
        text="BẮT ĐẦU ĐƠN MỚI",
        command=on_new_order if on_new_order is not None else lambda: None,
        font=("Segoe UI", 12, "bold"),
        fg="white",
        bg=PRIMARY_COLOR,
        activeforeground="white",
        activebackground=PRIMARY_DARK,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=13,
    )
    ui["new_order_button"].grid(row=4, column=0, padx=24, pady=(0, 24), sticky="ew")


def _create_info_row(parent, row, title, value_var):
    row_frame = tk.Frame(parent, bg=CARD_COLOR)
    row_frame.grid(row=row, column=0, padx=24, pady=4, sticky="ew")
    row_frame.grid_columnconfigure(1, weight=1)
    tk.Label(
        row_frame,
        text=title,
        font=("Segoe UI", 10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR,
    ).grid(row=0, column=0, sticky="w")
    tk.Label(
        row_frame,
        textvariable=value_var,
        font=("Segoe UI", 13, "bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR,
    ).grid(row=0, column=1, sticky="e")


def _draw_camera_placeholder(ui, event=None):
    canvas = ui["camera_canvas"]
    width = event.width if event is not None else canvas.winfo_width()
    height = event.height if event is not None else canvas.winfo_height()

    if ui["camera_photo"] is not None:
        canvas.coords(ui["camera_image_id"], width / 2, height / 2)
        return

    canvas.delete("placeholder")
    canvas.create_text(
        width / 2,
        height / 2 - 16,
        text="CAMERA",
        font=("Segoe UI", 20, "bold"),
        fill="#B6C8E1",
        tags="placeholder",
    )
    canvas.create_text(
        width / 2,
        height / 2 + 18,
        text="Hình ảnh trực tiếp sẽ hiển thị tại đây",
        font=("Segoe UI", 10),
        fill="#7F97B7",
        tags="placeholder",
    )

    image_scale = min(width / FRAME_WIDTH, height / FRAME_HEIGHT)
    image_left = (width - FRAME_WIDTH * image_scale) / 2
    image_top = (height - FRAME_HEIGHT * image_scale) / 2
    canvas.create_rectangle(
        image_left + SCALE_X1 * image_scale,
        image_top + SCALE_Y1 * image_scale,
        image_left + SCALE_X2 * image_scale,
        image_top + SCALE_Y2 * image_scale,
        outline="#38BDF8",
        width=2,
        dash=(9, 6),
        tags="placeholder",
    )
    canvas.create_text(
        image_left + SCALE_X1 * image_scale + 12,
        image_top + SCALE_Y1 * image_scale + 12,
        text="ROI MẶT CÂN",
        anchor="nw",
        font=("Segoe UI", 9, "bold"),
        fill="#7DD3FC",
        tags="placeholder",
    )


def update_camera(ui, photo_image):
    canvas = ui["camera_canvas"]
    ui["camera_photo"] = photo_image
    if photo_image is None:
        canvas.itemconfigure(ui["camera_image_id"], image="")
        _draw_camera_placeholder(ui)
        return

    canvas.delete("placeholder")
    canvas.itemconfigure(ui["camera_image_id"], image=photo_image)
    canvas.coords(
        ui["camera_image_id"],
        canvas.winfo_width() / 2,
        canvas.winfo_height() / 2,
    )


def update_product_info(ui, fruit_name=None, weight_g=0, price_per_kg=0, total=0):
    ui["fruit_var"].set(fruit_name if fruit_name else "Chưa xác định")
    ui["weight_var"].set(f"{int(weight_g)} g")
    ui["price_var"].set(format_money(price_per_kg) + "/kg")
    ui["total_var"].set(format_money(total))


def update_cart(ui, items, total):
    ui["cart_count"] = len(items)
    listbox = ui["cart_listbox"]
    listbox.delete(0, tk.END)
    for index, item in enumerate(items, start=1):
        item_total = format_money(item["item_total"])
        listbox.insert(
            tk.END,
            f"{index}. {item['fruit_name']} - {int(item['weight_g'])} g - {item_total}",
        )
    ui["cart_total_var"].set(f"Tổng hóa đơn: {format_money(total)}")


def set_customer_state(ui, state):
    status_text, status_color, status_bg, instruction = STATE_STYLES.get(
        state,
        STATE_STYLES["EMPTY"],
    )
    ui["header_status"].configure(
        text=status_text,
        fg=status_color,
        bg=status_bg,
    )
    ui["instruction_var"].set(instruction)
    ui["add_item_button"].configure(
        state=tk.NORMAL if state == "READY_TO_ADD" else tk.DISABLED
    )
    can_pay = ui.get("cart_count", 0) > 0 and state == "EMPTY"
    ui["payment_button"].configure(
        state=tk.NORMAL if can_pay else tk.DISABLED
    )


def show_weighing_screen(ui):
    ui["weighing_screen"].tkraise()


def show_payment_qr(ui, qr_image, order_id, total, item_count):
    ui["order_id_var"].set(f"Mã đơn: {order_id}")
    ui["payment_items_var"].set(f"Số món: {item_count}")
    ui["payment_total_var"].set(format_money(total))
    set_qr_image(ui, qr_image)
    set_customer_state(ui, "SHOWING_PAYMENT_QR")
    ui["payment_screen"].tkraise()


def show_qr_screen(ui, qr_image, fruit_name, weight_g, price_per_kg, total, can_continue=False):
    """Compatibility wrapper for old demo calls."""
    show_payment_qr(ui, qr_image, "DEMO", total, 1)


def set_qr_image(ui, qr_image):
    if qr_image is None:
        ui["qr_photo"] = None
        ui["qr_image_label"].configure(image="", text="QR", width=11, height=6)
        return

    qr_size = ui["qr_size"]
    resized_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    qr_photo = ImageTk.PhotoImage(resized_image)
    ui["qr_photo"] = qr_photo
    ui["qr_image_label"].configure(
        image=qr_photo,
        text="",
        width=qr_size,
        height=qr_size,
    )


def run_demo():
    from cart import add_item, calculate_cart_total
    from qr import create_order_id, create_payment_qr_data, create_qr_image

    root = create_window()
    ui = create_customer_ui(root)
    demo_cart = []
    add_item(demo_cart, "Táo", 500, 36000)
    add_item(demo_cart, "Xoài", 850, 45000)
    update_cart(ui, demo_cart, calculate_cart_total(demo_cart))

    order_id = create_order_id()
    qr_data = create_payment_qr_data(order_id, calculate_cart_total(demo_cart))
    show_payment_qr(
        ui,
        create_qr_image(qr_data),
        order_id,
        calculate_cart_total(demo_cart),
        len(demo_cart),
    )
    root.mainloop()


if __name__ == "__main__":
    run_demo()
