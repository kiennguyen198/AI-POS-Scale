import cart

EMPTY="EMPTY"                       # cân trống
DETECTING="DETECTING"               # đang xác định loại quả    
MIXED_BLOCKED="MIXED_BLOCKED"       # có nhiều loại quả, không cho thêm
STABILIZING="STABILIZING"           # biết loại quả nhưng đang dao động
READY_TO_ADD="READY_TO_ADD"         # ổn định, cho nút thêm
WAIT_REMOVAL="WAIT_REMOVAL"         # đã được thêm, khóa nút và chờ lấy khỏi cân

def get_weighing_state(current_state,is_empty,has_mixed_fruits,stable_fruit,is_weight_stable):
    if current_state==WAIT_REMOVAL:
        if is_empty:
            return EMPTY

        return WAIT_REMOVAL

    if is_empty:
        return EMPTY

    if has_mixed_fruits:
        return MIXED_BLOCKED

    if stable_fruit is None:
        return DETECTING

    if not is_weight_stable:
        return STABILIZING

    return READY_TO_ADD

def add_current_item(current_state,cart_items,fruit_name,weight_g,price_per_kg):
    if current_state!=READY_TO_ADD:
        return current_state

    cart.add_item(cart_items,fruit_name,weight_g,price_per_kg)

    return WAIT_REMOVAL