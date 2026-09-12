"""QR helpers for the customer self-checkout prototype."""

from datetime import datetime

import qrcode


def create_order_id():
    """Create a unique order reference for one cart."""
    return "O" + datetime.now().strftime("%Y%m%d%H%M%S%f")


def create_payment_qr_data(order_id, total):
    """Create a demo payment payload for the complete cart.

    A real bank/provider payload is intentionally not hard-coded. The order
    reference and amount provide the information needed for a future payment
    webhook integration.
    """
    return f"AI_POS_PAYMENT|1|{order_id}|{int(total)}|VND|DEMO"


def create_qr_image(qr_data):
    return qrcode.make(qr_data)


# Legacy product-label helpers remain importable for the old cashier demo.
def create_label_id():
    return "L" + datetime.now().strftime("%Y%m%d%H%M%S%f")


def create_qr_data(label_id, fruit_name, weight_g, price_per_kg):
    return f"AI_POS|1|{label_id}|{fruit_name}|{weight_g}|{price_per_kg}"
