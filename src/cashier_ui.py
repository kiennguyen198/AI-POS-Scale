import ctypes
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

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


def create_window():
    _enable_dpi_awareness()
    root=tk.Tk()
    screen_dpi=root.winfo_fpixels("1i")
    root.tk.call("tk","scaling",screen_dpi/72)
    root.title("AI POS Scale - Màn hình thu ngân")
    root.geometry("1200x700")
    root.minsize(980,580)
    root.configure(bg=BG_COLOR)
    return root


def _create_brand_header(header,ui):
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
        text="QUẦY THU NGÂN",
        font=("Segoe UI",20,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).pack(anchor="w")


def create_cashier_ui(
    root,
    on_remove=None,
    on_clear=None,
    on_complete=None
):
    ui={}
    screen_width=root.winfo_screenwidth()
    screen_height=root.winfo_screenheight()
    compact=screen_width<=1100 or screen_height<=700
    ui["compact"]=compact

    header_height=72 if compact else 82
    content_pad=14 if compact else 24
    content_gap=12 if compact else 22

    _configure_tree_style(root)

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

    _create_brand_header(header,ui)

    ui["header_status"]=tk.Label(
        header,
        text="Sẵn sàng quét",
        font=("Segoe UI",11,"bold"),
        fg=PRIMARY_COLOR,
        bg="#E5EEFF",
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
    content.grid_columnconfigure(0,weight=2)
    content.grid_columnconfigure(1,weight=3)

    _create_scanner_panel(content,ui)
    _create_invoice_panel(
        content,
        ui,
        on_remove,
        on_clear,
        on_complete
    )

    set_scan_status(ui,"Sẵn sàng quét","ready")
    set_cart(ui,[])

    return ui


def _configure_tree_style(root):
    style=ttk.Style(root)

    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "Invoice.Treeview",
        background=CARD_COLOR,
        fieldbackground=CARD_COLOR,
        foreground=TEXT_COLOR,
        borderwidth=0,
        relief="flat",
        rowheight=42,
        font=("Segoe UI",10)
    )
    style.configure(
        "Invoice.Treeview.Heading",
        background="#E7EFFF",
        foreground=TEXT_COLOR,
        relief="flat",
        borderwidth=0,
        font=("Segoe UI",10,"bold"),
        padding=(8,10)
    )
    style.map(
        "Invoice.Treeview",
        background=[("selected","#DCE8FF")],
        foreground=[("selected",TEXT_COLOR)]
    )


def _create_scanner_panel(content,ui):
    scanner_card=tk.Frame(
        content,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    scanner_card.grid(row=0,column=0,padx=(0,12),sticky="nsew")
    scanner_card.grid_rowconfigure(1,weight=1)
    scanner_card.grid_columnconfigure(0,weight=1)

    tk.Label(
        scanner_card,
        text="CAMERA QUÉT QR",
        font=("Segoe UI",12,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=0,padx=20,pady=(18,12),sticky="w")

    camera_canvas=tk.Canvas(
        scanner_card,
        bg=CAMERA_COLOR,
        highlightthickness=0
    )
    camera_canvas.grid(row=1,column=0,padx=20,sticky="nsew")

    ui["camera_canvas"]=camera_canvas
    ui["camera_image_id"]=camera_canvas.create_image(0,0,anchor="center")
    ui["camera_photo"]=None
    camera_canvas.bind(
        "<Configure>",
        lambda event:_draw_scanner_placeholder(ui,event)
    )

    status_frame=tk.Frame(scanner_card,bg="#EAF1FF")
    status_frame.grid(row=2,column=0,padx=20,pady=16,sticky="ew")
    status_frame.grid_columnconfigure(0,weight=1)
    ui["scan_status_frame"]=status_frame

    ui["scan_status_var"]=tk.StringVar(value="Sẵn sàng quét")

    ui["scan_status_label"]=tk.Label(
        status_frame,
        textvariable=ui["scan_status_var"],
        font=("Segoe UI",11,"bold"),
        fg=PRIMARY_COLOR,
        bg="#EAF1FF"
    )
    ui["scan_status_label"].grid(
        row=0,
        column=0,
        padx=14,
        pady=(12,3),
        sticky="w"
    )

    ui["scan_instruction_label"]=tk.Label(
        status_frame,
        text="Đưa từng mã QR vào giữa khung hình và chờ xác nhận.",
        font=("Segoe UI",9),
        fg=MUTED_COLOR,
        bg="#EAF1FF",
        justify="left",
        wraplength=350
    )
    ui["scan_instruction_label"].grid(
        row=1,
        column=0,
        padx=14,
        pady=(0,12),
        sticky="w"
    )


def _create_invoice_panel(
    content,
    ui,
    on_remove,
    on_clear,
    on_complete
):
    invoice_card=tk.Frame(
        content,
        bg=CARD_COLOR,
        highlightthickness=1,
        highlightbackground=BORDER_COLOR
    )
    invoice_card.grid(row=0,column=1,padx=(12,0),sticky="nsew")
    invoice_card.grid_rowconfigure(1,weight=1)
    invoice_card.grid_columnconfigure(0,weight=1)

    title_frame=tk.Frame(invoice_card,bg=CARD_COLOR)
    title_frame.grid(row=0,column=0,padx=22,pady=(18,12),sticky="ew")
    title_frame.grid_columnconfigure(1,weight=1)

    tk.Label(
        title_frame,
        text="HÓA ĐƠN HIỆN TẠI",
        font=("Segoe UI",13,"bold"),
        fg=TEXT_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=0,sticky="w")

    ui["item_count_var"]=tk.StringVar(value="0 sản phẩm")
    tk.Label(
        title_frame,
        textvariable=ui["item_count_var"],
        font=("Segoe UI",10),
        fg=MUTED_COLOR,
        bg=CARD_COLOR
    ).grid(row=0,column=1,sticky="e")

    table_frame=tk.Frame(invoice_card,bg=CARD_COLOR)
    table_frame.grid(row=1,column=0,padx=22,sticky="nsew")
    table_frame.grid_rowconfigure(0,weight=1)
    table_frame.grid_columnconfigure(0,weight=1)

    columns=("fruit_name","weight_g","price_per_kg","item_total")
    tree=ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        style="Invoice.Treeview",
        selectmode="browse"
    )
    tree.heading("fruit_name",text="Trái cây")
    tree.heading("weight_g",text="Khối lượng")
    tree.heading("price_per_kg",text="Đơn giá")
    tree.heading("item_total",text="Thành tiền")

    tree.column("fruit_name",width=135,minwidth=110,anchor="w")
    tree.column("weight_g",width=100,minwidth=85,anchor="center")
    tree.column("price_per_kg",width=125,minwidth=110,anchor="e")
    tree.column("item_total",width=135,minwidth=120,anchor="e")

    scrollbar=ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=tree.yview
    )
    tree.configure(yscrollcommand=scrollbar.set)

    tree.grid(row=0,column=0,sticky="nsew")
    scrollbar.grid(row=0,column=1,sticky="ns")

    tree.tag_configure("even",background="#F7FAFF")
    tree.tag_configure("odd",background=CARD_COLOR)
    tree.bind(
        "<<TreeviewSelect>>",
        lambda event:_update_remove_button(ui)
    )

    ui["cart_tree"]=tree

    total_frame=tk.Frame(invoice_card,bg="#EAF1FF")
    total_frame.grid(row=2,column=0,padx=22,pady=(14,12),sticky="ew")
    total_frame.grid_columnconfigure(1,weight=1)

    tk.Label(
        total_frame,
        text="TỔNG HÓA ĐƠN",
        font=("Segoe UI",11,"bold"),
        fg=MUTED_COLOR,
        bg="#EAF1FF"
    ).grid(row=0,column=0,padx=18,pady=16,sticky="w")

    ui["cart_total_var"]=tk.StringVar(value="0 đ")
    tk.Label(
        total_frame,
        textvariable=ui["cart_total_var"],
        font=("Segoe UI",22,"bold"),
        fg=PRIMARY_DARK,
        bg="#EAF1FF"
    ).grid(row=0,column=1,padx=18,pady=12,sticky="e")

    action_frame=tk.Frame(invoice_card,bg=CARD_COLOR)
    action_frame.grid(row=3,column=0,padx=22,pady=(0,22),sticky="ew")

    for column in range(3):
        action_frame.grid_columnconfigure(column,weight=1)

    ui["remove_button"]=tk.Button(
        action_frame,
        text="XÓA MÓN",
        command=lambda:_request_remove(ui,on_remove),
        font=("Segoe UI",10,"bold"),
        fg=DANGER_COLOR,
        bg="#FDE8E7",
        activeforeground=DANGER_COLOR,
        activebackground="#F8D4D2",
        disabledforeground="#A8B2AE",
        relief="flat",
        cursor="hand2",
        pady=11,
        state=tk.DISABLED
    )
    ui["remove_button"].grid(row=0,column=0,padx=(0,6),sticky="ew")

    ui["clear_button"]=tk.Button(
        action_frame,
        text="HỦY HÓA ĐƠN",
        command=lambda:_request_action(on_clear),
        font=("Segoe UI",10,"bold"),
        fg=TEXT_COLOR,
        bg="#E7EFFF",
        activeforeground=TEXT_COLOR,
        activebackground="#D6E4FF",
        disabledforeground="#A8B2AE",
        relief="flat",
        cursor="hand2",
        pady=11,
        state=tk.DISABLED
    )
    ui["clear_button"].grid(row=0,column=1,padx=6,sticky="ew")

    ui["complete_button"]=tk.Button(
        action_frame,
        text="HOÀN TẤT",
        command=lambda:_request_action(on_complete),
        font=("Segoe UI",10,"bold"),
        fg="white",
        bg=PRIMARY_COLOR,
        activeforeground="white",
        activebackground=PRIMARY_DARK,
        disabledforeground="#A8B2AE",
        relief="flat",
        cursor="hand2",
        pady=11,
        state=tk.DISABLED
    )
    ui["complete_button"].grid(row=0,column=2,padx=(6,0),sticky="ew")


def _draw_scanner_placeholder(ui,event=None):
    canvas=ui["camera_canvas"]
    width=event.width if event is not None else canvas.winfo_width()
    height=event.height if event is not None else canvas.winfo_height()

    if ui["camera_photo"] is not None:
        canvas.coords(ui["camera_image_id"],width/2,height/2)
        return

    canvas.delete("placeholder")

    target_size=min(width,height)*0.56
    left=(width-target_size)/2
    top=(height-target_size)/2
    right=left+target_size
    bottom=top+target_size
    corner=max(24,target_size*0.16)

    line_options={
        "fill":"#38BDF8",
        "width":3,
        "tags":"placeholder"
    }

    canvas.create_line(left,top,left+corner,top,**line_options)
    canvas.create_line(left,top,left,top+corner,**line_options)
    canvas.create_line(right,top,right-corner,top,**line_options)
    canvas.create_line(right,top,right,top+corner,**line_options)
    canvas.create_line(left,bottom,left+corner,bottom,**line_options)
    canvas.create_line(left,bottom,left,bottom-corner,**line_options)
    canvas.create_line(right,bottom,right-corner,bottom,**line_options)
    canvas.create_line(right,bottom,right,bottom-corner,**line_options)

    canvas.create_text(
        width/2,
        height/2-10,
        text="QR",
        font=("Segoe UI",28,"bold"),
        fill="#B6C8E1",
        tags="placeholder"
    )
    canvas.create_text(
        width/2,
        height/2+26,
        text="Đặt mã vào giữa khung",
        font=("Segoe UI",10),
        fill="#7F97B7",
        tags="placeholder"
    )


def update_camera(ui,photo_image):
    canvas=ui["camera_canvas"]
    ui["camera_photo"]=photo_image

    if photo_image is None:
        canvas.itemconfigure(ui["camera_image_id"],image="")
        _draw_scanner_placeholder(ui)
        return

    canvas.delete("placeholder")
    canvas.itemconfigure(ui["camera_image_id"],image=photo_image)
    canvas.coords(
        ui["camera_image_id"],
        canvas.winfo_width()/2,
        canvas.winfo_height()/2
    )


def set_scan_status(ui,message,tone="ready"):
    tones={
        "ready":(PRIMARY_COLOR,"#E5EEFF"),
        "success":(PRIMARY_COLOR,"#E5EEFF"),
        "warning":("#986319","#FFF3D7"),
        "error":(DANGER_COLOR,"#FDE8E7")
    }
    color,background=tones.get(tone,tones["ready"])

    ui["scan_status_var"].set(message)
    ui["scan_status_label"].configure(fg=color,bg=background)
    ui["scan_status_frame"].configure(bg=background)
    ui["scan_instruction_label"].configure(bg=background)
    ui["header_status"].configure(text=message,fg=color,bg=background)


def set_cart(ui,cart):
    tree=ui["cart_tree"]

    for row_id in tree.get_children():
        tree.delete(row_id)

    cart_total=0

    for index,item in enumerate(cart):
        item_total=item.get(
            "item_total",
            round(item["price_per_kg"]*item["weight_g"]/1000)
        )
        cart_total+=item_total
        row_tag="even" if index%2==0 else "odd"

        tree.insert(
            "",
            "end",
            values=(
                item["fruit_name"],
                f'{int(item["weight_g"])} g',
                format_money(item["price_per_kg"])+"/kg",
                format_money(item_total)
            ),
            tags=(row_tag,)
        )

    item_count=len(cart)
    count_text=f"{item_count} sản phẩm"
    ui["item_count_var"].set(count_text)
    ui["cart_total_var"].set(format_money(cart_total))

    has_items=item_count>0
    action_state=tk.NORMAL if has_items else tk.DISABLED
    ui["clear_button"].configure(state=action_state)
    ui["complete_button"].configure(state=action_state)
    ui["remove_button"].configure(state=tk.DISABLED)


def get_selected_index(ui):
    selected_rows=ui["cart_tree"].selection()

    if not selected_rows:
        return None

    return ui["cart_tree"].index(selected_rows[0])


def _update_remove_button(ui):
    selected_index=get_selected_index(ui)
    state=tk.NORMAL if selected_index is not None else tk.DISABLED
    ui["remove_button"].configure(state=state)


def _request_remove(ui,on_remove):
    selected_index=get_selected_index(ui)

    if selected_index is None:
        set_scan_status(ui,"Hãy chọn món cần xóa","warning")
        return

    if on_remove is not None:
        on_remove(selected_index)


def _request_action(callback):
    if callback is not None:
        callback()


def run_demo():
    demo_cart=[
        {
            "fruit_name":"Xoài",
            "weight_g":850,
            "price_per_kg":45000,
            "item_total":38250
        },
        {
            "fruit_name":"Cam",
            "weight_g":600,
            "price_per_kg":28000,
            "item_total":16800
        },
        {
            "fruit_name":"Táo",
            "weight_g":500,
            "price_per_kg":35000,
            "item_total":17500
        }
    ]

    root=create_window()
    ui={}

    def remove_demo_item(item_index):
        demo_cart.pop(item_index)
        set_cart(ui,demo_cart)
        set_scan_status(ui,"Đã xóa món khỏi hóa đơn","success")

    def clear_demo_cart():
        demo_cart.clear()
        set_cart(ui,demo_cart)
        set_scan_status(ui,"Hóa đơn đã được hủy","warning")

    def complete_demo_cart():
        demo_cart.clear()
        set_cart(ui,demo_cart)
        set_scan_status(ui,"Hóa đơn đã hoàn tất","success")

    ui=create_cashier_ui(
        root,
        on_remove=remove_demo_item,
        on_clear=clear_demo_cart,
        on_complete=complete_demo_cart
    )
    set_cart(ui,demo_cart)

    root.mainloop()


if __name__=="__main__":
    run_demo()
