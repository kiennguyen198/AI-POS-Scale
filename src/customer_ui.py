import ctypes
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk


BG_COLOR="#F3F7FF"
CARD_COLOR="#FFFFFF"
TEXT_COLOR="#12335B"
MUTED_COLOR="#64748B"
PRIMARY_COLOR="#2F6BFF"
PRIMARY_DARK="#1647B8"
BORDER_COLOR="#D7E3F4"
DANGER_COLOR="#C2413A"
CAMERA_COLOR="#0A1E38"

PROJECT_ROOT=Path(__file__).resolve().parent.parent
UIT_LOGO_PATH=PROJECT_ROOT/"images"/"uit_logo_vietnamese.png"


STATE_STYLES={
    "EMPTY":(
        "Cân đang trống",
        "#5F6B67",
        "#E8EEEB",
        "Đặt một túi trái cây vào đúng vùng mặt cân."
    ),
    "DETECTING":(
        "Đang nhận diện",
        "#986319",
        "#FFF3D7",
        "Giữ túi đứng yên để hệ thống xác định loại trái cây."
    ),
    "MIXED_BLOCKED":(
        "Nhiều loại trái cây",
        DANGER_COLOR,
        "#FDE8E7",
        "Mỗi túi chỉ được chứa một loại trái cây."
    ),
    "STABILIZING":(
        "Đang ổn định",
        "#24649A",
        "#E4F1FB",
        "Không chạm vào túi trong lúc hệ thống chốt khối lượng."
    ),
    "READY_TO_QR":(
        "Sẵn sàng tạo QR",
        PRIMARY_COLOR,
        "#E5EEFF",
        "Thông tin đã ổn định. Bạn có thể tạo QR cho túi này."
    ),
    "SHOWING_QR":(
        "QR đã được tạo",
        PRIMARY_COLOR,
        "#E5EEFF",
        "Đưa QR cho nhân viên quét, sau đó lấy túi khỏi cân."
    )
}


def format_money(value):
    return f"{int(value):,}".replace(",",".")+" đ"


def _enable_dpi_awareness():
    if sys.platform!="win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError,OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError,OSError):
            pass


def create_window(fullscreen=False):
    _enable_dpi_awareness()
    root=tk.Tk()
    screen_dpi=root.winfo_fpixels("1i")
    root.tk.call("tk","scaling",screen_dpi/72)
    root.title("AI POS Scale - Màn hình khách hàng")
    root.geometry("1100x650")
    root.minsize(900,540)
    root.configure(bg=BG_COLOR)

    if fullscreen:
        root.attributes("-fullscreen",True)

    root.bind(
        "<Escape>",
        lambda event:root.attributes("-fullscreen",False)
    )
    return root


def _create_brand_header(header,ui,subtitle):
    brand_frame=tk.Frame(header,bg=CARD_COLOR)
    brand_frame.place(x=24,rely=0.5,anchor="w")

    if UIT_LOGO_PATH.exists():
        logo_image=Image.open(UIT_LOGO_PATH)
        logo_size=(150,54) if ui["compact"] else (180,65)
        logo_image.thumbnail(logo_size,Image.Resampling.LANCZOS)
        logo_photo=ImageTk.PhotoImage(logo_image)
        ui["uit_logo_photo"]=logo_photo

        tk.Label(
            brand_frame,
            image=logo_photo,
            bg=CARD_COLOR,
            bd=0
        ).pack(side="left")
    else:
        tk.Label(
            brand_frame,
            text="UIT",
            font=("Segoe UI",22,"bold"),
            fg=PRIMARY_COLOR,
            bg=CARD_COLOR
        ).pack(side="left")

    product_frame=tk.Frame(header,bg=CARD_COLOR)
    product_frame.place(relx=0.5,rely=0.5,anchor="center")

    tk.Label(
        product_frame,
        text="AI POS SCALE",
        font=("Segoe UI",15,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).pack(anchor="w")

    tk.Label(
        product_frame,
        text=subtitle,
        font=("Segoe UI",9),
        fg=MUTED_COLOR,
        bg=CARD_COLOR
    ).pack(anchor="w")


def create_customer_ui(root,on_create_qr=None,on_next=None):
    ui={}
    screen_width=root.winfo_screenwidth()
    screen_height=root.winfo_screenheight()
    compact=screen_width<=1100 or screen_height<=700
    ui["compact"]=compact
    ui["qr_size"]=260 if compact else 330

    header_height=72 if compact else 82
    content_pad=14 if compact else 24
    content_gap=12 if compact else 22

    root.grid_rowconfigure(1,weight=1)
    root.grid_columnconfigure(0,weight=1)

    header=tk.Frame(
        root,
        bg=CARD_COLOR,
        height=header_height,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    header.grid(row=0,column=0,sticky="ew")
    header.grid_propagate(False)

    _create_brand_header(header,ui,"Cân trái cây thông minh")

    ui["header_status"]=tk.Label(
        header,
        text="Cân đang trống",
        font=("Segoe UI",11,"bold"),
        fg="#5F6B67",
        bg="#E8EEEB",
        padx=18,
        pady=9
    )
    ui["header_status"].place(
        relx=1.0,
        x=-content_pad,
        rely=0.5,
        anchor="e"
    )

    content=tk.Frame(root,bg=BG_COLOR)
    content.grid(
        row=1,
        column=0,
        padx=content_pad,
        pady=content_gap,
        sticky="nsew"
    )
    content.grid_rowconfigure(0,weight=1)
    content.grid_columnconfigure(0,weight=1)

    weighing_screen=tk.Frame(content,bg=BG_COLOR)
    weighing_screen.grid(row=0,column=0,sticky="nsew")
    weighing_screen.grid_rowconfigure(0,weight=1)
    weighing_screen.grid_columnconfigure(0,weight=3)
    weighing_screen.grid_columnconfigure(1,weight=2)

    qr_screen=tk.Frame(content,bg=BG_COLOR)
    qr_screen.grid(row=0,column=0,sticky="nsew")
    qr_screen.grid_rowconfigure(0,weight=1)
    qr_screen.grid_columnconfigure(0,weight=3)
    qr_screen.grid_columnconfigure(1,weight=2)

    ui["weighing_screen"]=weighing_screen
    ui["qr_screen"]=qr_screen

    _create_weighing_screen(ui,on_create_qr)
    _create_qr_screen(ui,on_next)

    show_weighing_screen(ui)
    set_customer_state(ui,"EMPTY")

    return ui


def _create_weighing_screen(ui,on_create_qr):
    screen=ui["weighing_screen"]

    camera_card=tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    camera_card.grid(row=0,column=0,padx=(0,12),sticky="nsew")
    camera_card.grid_rowconfigure(1,weight=1)
    camera_card.grid_columnconfigure(0,weight=1)

    camera_header=tk.Frame(camera_card,bg=CARD_COLOR)
    camera_header.grid(row=0,column=0,padx=20,pady=(16,12),sticky="ew")

    tk.Label(
        camera_header,
        text="CAMERA TRỰC TIẾP",
        font=("Segoe UI",12,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).pack(side="left")

    tk.Label(
        camera_header,
        text="Vùng mặt cân",
        font=("Segoe UI",9,"bold"),
        fg=PRIMARY_COLOR,
        bg="#E7EFFF",
        padx=10,
        pady=5
    ).pack(side="right")

    camera_canvas=tk.Canvas(
        camera_card,
        bg=CAMERA_COLOR,
        highlightthickness=0
    )
    camera_canvas.grid(row=1,column=0,padx=20,pady=(0,16),sticky="nsew")

    ui["camera_canvas"]=camera_canvas
    ui["camera_image_id"]=camera_canvas.create_image(0,0,anchor="center")
    ui["camera_photo"]=None
    camera_canvas.bind(
        "<Configure>",
        lambda event:_draw_camera_placeholder(ui,event)
    )

    info_card=tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    info_card.grid(row=0,column=1,padx=(12,0),sticky="nsew")
    info_card.grid_columnconfigure(0,weight=1)

    tk.Label(
        info_card,
        text="THÔNG TIN TÚI TRÁI CÂY",
        font=("Segoe UI",12,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=0,padx=24,pady=(22,16),sticky="w")

    ui["fruit_var"]=tk.StringVar(value="Chưa xác định")
    ui["weight_var"]=tk.StringVar(value="0 g")
    ui["price_var"]=tk.StringVar(value="0 đ/kg")
    ui["total_var"]=tk.StringVar(value="0 đ")
    ui["instruction_var"]=tk.StringVar()

    _create_info_row(info_card,1,"Loại trái cây",ui["fruit_var"])
    _create_info_row(info_card,2,"Khối lượng",ui["weight_var"])
    _create_info_row(info_card,3,"Đơn giá",ui["price_var"])

    total_frame=tk.Frame(info_card,bg="#EAF1FF")
    total_frame.grid(row=4,column=0,padx=24,pady=(18,14),sticky="ew")

    tk.Label(
        total_frame,
        text="THÀNH TIỀN",
        font=("Segoe UI",10,"bold"),
        fg=MUTED_COLOR,
        bg="#EAF1FF"
    ).pack(anchor="w",padx=18,pady=(14,2))

    tk.Label(
        total_frame,
        textvariable=ui["total_var"],
        font=("Segoe UI",25,"bold"),
        fg=PRIMARY_DARK,
        bg="#EAF1FF"
    ).pack(anchor="w",padx=18,pady=(0,14))

    instruction=tk.Label(
        info_card,
        textvariable=ui["instruction_var"],
        font=("Segoe UI",10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR,
        justify="left",
        wraplength=330
    )
    instruction.grid(row=5,column=0,padx=24,pady=(2,14),sticky="w")

    ui["create_qr_button"]=tk.Button(
        info_card,
        text="TẠO QR",
        command=on_create_qr if on_create_qr is not None else lambda:None,
        font=("Segoe UI",12,"bold"),
        fg="white",
        bg=PRIMARY_COLOR,
        activeforeground="white",
        activebackground=PRIMARY_DARK,
        disabledforeground="#A8B2AE",
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=13
    )
    ui["create_qr_button"].grid(
        row=6,
        column=0,
        padx=24,
        pady=(0,24),
        sticky="ew"
    )


def _create_qr_screen(ui,on_next):
    screen=ui["qr_screen"]

    qr_card=tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    qr_card.grid(row=0,column=0,padx=(0,12),sticky="nsew")
    qr_card.grid_rowconfigure(1,weight=1)
    qr_card.grid_columnconfigure(0,weight=1)

    tk.Label(
        qr_card,
        text="ĐƯA MÃ QR CHO NHÂN VIÊN QUÉT",
        font=("Segoe UI",13,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=0,pady=(22,8))

    ui["qr_image_label"]=tk.Label(
        qr_card,
        text="QR",
        font=("Segoe UI",36,"bold"),
        fg=MUTED_COLOR,
        bg="white",
        width=11,
        height=6,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    ui["qr_image_label"].grid(row=1,column=0,padx=28,pady=14)
    ui["qr_photo"]=None

    tk.Label(
        qr_card,
        text="Giữ màn hình hướng về phía webcam của quầy thu ngân",
        font=("Segoe UI",10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR
    ).grid(row=2,column=0,pady=(0,22))

    summary_card=tk.Frame(
        screen,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    summary_card.grid(row=0,column=1,padx=(12,0),sticky="nsew")
    summary_card.grid_columnconfigure(0,weight=1)

    tk.Label(
        summary_card,
        text="THÔNG TIN ĐÃ CHỐT",
        font=("Segoe UI",12,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=0,padx=24,pady=(22,16),sticky="w")

    ui["qr_fruit_var"]=tk.StringVar(value="-")
    ui["qr_weight_var"]=tk.StringVar(value="0 g")
    ui["qr_price_var"]=tk.StringVar(value="0 đ/kg")
    ui["qr_total_var"]=tk.StringVar(value="0 đ")
    ui["next_hint_var"]=tk.StringVar(
        value="Hãy lấy túi khỏi cân trước khi tiếp tục."
    )

    _create_info_row(summary_card,1,"Loại trái cây",ui["qr_fruit_var"])
    _create_info_row(summary_card,2,"Khối lượng",ui["qr_weight_var"])
    _create_info_row(summary_card,3,"Đơn giá",ui["qr_price_var"])

    total_frame=tk.Frame(summary_card,bg="#EAF1FF")
    total_frame.grid(row=4,column=0,padx=24,pady=(18,14),sticky="ew")

    tk.Label(
        total_frame,
        text="THÀNH TIỀN",
        font=("Segoe UI",10,"bold"),
        fg=MUTED_COLOR,
        bg="#EAF1FF"
    ).pack(anchor="w",padx=18,pady=(14,2))

    tk.Label(
        total_frame,
        textvariable=ui["qr_total_var"],
        font=("Segoe UI",25,"bold"),
        fg=PRIMARY_DARK,
        bg="#EAF1FF"
    ).pack(anchor="w",padx=18,pady=(0,14))

    tk.Label(
        summary_card,
        textvariable=ui["next_hint_var"],
        font=("Segoe UI",10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR,
        justify="left",
        wraplength=330
    ).grid(row=5,column=0,padx=24,pady=(2,14),sticky="w")

    ui["next_button"]=tk.Button(
        summary_card,
        text="CÂN TÚI TIẾP THEO",
        command=on_next if on_next is not None else lambda:None,
        font=("Segoe UI",12,"bold"),
        fg="white",
        bg=PRIMARY_COLOR,
        activeforeground="white",
        activebackground=PRIMARY_DARK,
        disabledforeground="#A8B2AE",
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=13,
        state=tk.DISABLED
    )
    ui["next_button"].grid(
        row=6,
        column=0,
        padx=24,
        pady=(0,24),
        sticky="ew"
    )


def _create_info_row(parent,row,title,value_var):
    row_frame=tk.Frame(parent,bg=CARD_COLOR)
    row_frame.grid(row=row,column=0,padx=24,pady=5,sticky="ew")
    row_frame.grid_columnconfigure(1,weight=1)

    tk.Label(
        row_frame,
        text=title,
        font=("Segoe UI",10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=0,sticky="w")

    tk.Label(
        row_frame,
        textvariable=value_var,
        font=("Segoe UI",13,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=1,sticky="e")


def _draw_camera_placeholder(ui,event=None):
    canvas=ui["camera_canvas"]
    width=event.width if event is not None else canvas.winfo_width()
    height=event.height if event is not None else canvas.winfo_height()

    if ui["camera_photo"] is not None:
        canvas.coords(ui["camera_image_id"],width/2,height/2)
        return

    canvas.delete("placeholder")

    canvas.create_text(
        width/2,
        height/2-16,
        text="CAMERA",
        font=("Segoe UI",20,"bold"),
        fill="#B6C8E1",
        tags="placeholder"
    )
    canvas.create_text(
        width/2,
        height/2+18,
        text="Hình ảnh trực tiếp sẽ hiển thị tại đây",
        font=("Segoe UI",10),
        fill="#7F97B7",
        tags="placeholder"
    )

    margin_x=max(45,width*0.16)
    margin_y=max(38,height*0.15)
    canvas.create_rectangle(
        margin_x,
        margin_y,
        width-margin_x,
        height-margin_y,
        outline="#38BDF8",
        width=2,
        dash=(9,6),
        tags="placeholder"
    )
    canvas.create_text(
        margin_x+12,
        margin_y+12,
        text="ROI MẶT CÂN",
        anchor="nw",
        font=("Segoe UI",9,"bold"),
        fill="#7DD3FC",
        tags="placeholder"
    )


def update_camera(ui,photo_image):
    canvas=ui["camera_canvas"]
    ui["camera_photo"]=photo_image

    if photo_image is None:
        canvas.itemconfigure(ui["camera_image_id"],image="")
        _draw_camera_placeholder(ui)
        return

    canvas.delete("placeholder")
    canvas.itemconfigure(ui["camera_image_id"],image=photo_image)
    canvas.coords(
        ui["camera_image_id"],
        canvas.winfo_width()/2,
        canvas.winfo_height()/2
    )


def update_product_info(ui,fruit_name=None,weight_g=0,price_per_kg=0,total=0):
    ui["fruit_var"].set(fruit_name if fruit_name else "Chưa xác định")
    ui["weight_var"].set(f"{int(weight_g)} g")
    ui["price_var"].set(format_money(price_per_kg)+"/kg")
    ui["total_var"].set(format_money(total))


def set_customer_state(ui,state):
    status_text,status_color,status_bg,instruction=STATE_STYLES.get(
        state,
        STATE_STYLES["EMPTY"]
    )

    ui["header_status"].configure(
        text=status_text,
        fg=status_color,
        bg=status_bg
    )
    ui["instruction_var"].set(instruction)
    set_create_qr_enabled(ui,state=="READY_TO_QR")


def set_create_qr_enabled(ui,enabled):
    state=tk.NORMAL if enabled else tk.DISABLED
    ui["create_qr_button"].configure(state=state)


def show_weighing_screen(ui):
    ui["weighing_screen"].tkraise()


def show_qr_screen(
    ui,
    qr_image,
    fruit_name,
    weight_g,
    price_per_kg,
    total,
    can_continue=False
):
    ui["qr_fruit_var"].set(fruit_name)
    ui["qr_weight_var"].set(f"{int(weight_g)} g")
    ui["qr_price_var"].set(format_money(price_per_kg)+"/kg")
    ui["qr_total_var"].set(format_money(total))

    set_qr_image(ui,qr_image)
    set_next_enabled(ui,can_continue)
    set_customer_state(ui,"SHOWING_QR")
    ui["qr_screen"].tkraise()


def set_qr_image(ui,qr_image):
    if qr_image is None:
        ui["qr_photo"]=None
        ui["qr_image_label"].configure(
            image="",
            text="QR",
            width=11,
            height=6
        )
        return

    qr_size=ui["qr_size"]
    resized_image=qr_image.resize(
        (qr_size,qr_size),
        Image.Resampling.LANCZOS
    )
    qr_photo=ImageTk.PhotoImage(resized_image)
    ui["qr_photo"]=qr_photo
    ui["qr_image_label"].configure(
        image=qr_photo,
        text="",
        width=qr_size,
        height=qr_size
    )


def set_next_enabled(ui,enabled):
    state=tk.NORMAL if enabled else tk.DISABLED
    ui["next_button"].configure(state=state)

    if enabled:
        ui["next_hint_var"].set(
            "Cân đã trở về 0 g. Bạn có thể bắt đầu túi tiếp theo."
        )
    else:
        ui["next_hint_var"].set(
            "Hãy lấy túi khỏi cân trước khi tiếp tục."
        )


def run_demo():
    from qr import create_label_id,create_qr_data,create_qr_image

    root=create_window()
    ui=create_customer_ui(root)

    demo_fruit="Xoài"
    demo_weight=850
    demo_price=45000
    demo_total=round(demo_weight*demo_price/1000)

    update_product_info(
        ui,
        demo_fruit,
        demo_weight,
        demo_price,
        demo_total
    )
    set_customer_state(ui,"READY_TO_QR")

    def create_demo_qr():
        label_id=create_label_id()
        qr_data=create_qr_data(
            label_id,
            "mango",
            demo_weight,
            demo_price
        )
        qr_image=create_qr_image(qr_data)
        show_qr_screen(
            ui,
            qr_image,
            demo_fruit,
            demo_weight,
            demo_price,
            demo_total
        )
        root.after(2500,lambda:set_next_enabled(ui,True))

    def next_demo_weighing():
        show_weighing_screen(ui)
        update_product_info(ui)
        set_customer_state(ui,"EMPTY")

    ui["create_qr_button"].configure(command=create_demo_qr)
    ui["next_button"].configure(command=next_demo_weighing)

    root.mainloop()


if __name__=="__main__":
    run_demo()
