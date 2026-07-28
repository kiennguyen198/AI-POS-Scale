EMPTY="EMPTY"                       # cân trống
DETECTING="DETECTING"               # đang xác định loại quả    
MIXED_BLOCKED="MIXED_BLOCKED"       # có nhiều loại quả, không cho thêm
STABILIZING="STABILIZING"           # biết loại quả nhưng đang dao động
READY_TO_QR="READY_TO_QR"
SHOWING_QR="SHOWING_QR"

def get_qr_state(current_state,is_empty,has_mixed_fruits,stable_fruit,is_weight_stable):
    if current_state==SHOWING_QR:
        return SHOWING_QR

    if is_empty:
        return EMPTY

    if has_mixed_fruits:
        return MIXED_BLOCKED

    if stable_fruit is None:
        return DETECTING

    if not is_weight_stable:
        return STABILIZING

    return READY_TO_QR

def show_qr(current_state):
    if current_state!=READY_TO_QR:
        return current_state
    return SHOWING_QR

def next_weighing(current_state,is_empty):
    if current_state!=SHOWING_QR:
        return current_state
    if not is_empty:
        return SHOWING_QR
    return EMPTY
