"""State transitions for the customer self-checkout scale."""

EMPTY = "EMPTY"
DETECTING = "DETECTING"
MIXED_BLOCKED = "MIXED_BLOCKED"
STABILIZING = "STABILIZING"
READY_TO_ADD = "READY_TO_ADD"
WAITING_REMOVAL = "WAITING_REMOVAL"
SHOWING_PAYMENT_QR = "SHOWING_PAYMENT_QR"

# Names kept for old demo/cashier imports.
READY_TO_QR = READY_TO_ADD
SHOWING_QR = SHOWING_PAYMENT_QR


def get_weighing_state(
    current_state,
    is_empty,
    has_mixed_fruits,
    stable_fruit,
    is_weight_stable,
):
    """Return the state of the item currently placed on the scale."""
    if current_state in (WAITING_REMOVAL, SHOWING_PAYMENT_QR):
        return current_state

    if is_empty:
        return EMPTY

    if has_mixed_fruits:
        return MIXED_BLOCKED

    if stable_fruit is None:
        return DETECTING

    if not is_weight_stable:
        return STABILIZING

    return READY_TO_ADD


def get_qr_state(
    current_state,
    is_empty,
    has_mixed_fruits,
    stable_fruit,
    is_weight_stable,
):
    """Compatibility wrapper for the previous label-QR implementation."""
    return get_weighing_state(
        current_state,
        is_empty,
        has_mixed_fruits,
        stable_fruit,
        is_weight_stable,
    )
