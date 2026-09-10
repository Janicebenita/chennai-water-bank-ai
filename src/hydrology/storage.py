"""Tank storage calculations."""


def available_storage_l(capacity_l: float, current_l: float) -> float:
    if capacity_l < 0 or current_l < 0:
        raise ValueError("storage values cannot be negative")
    return max(0.0, capacity_l - min(current_l, capacity_l))


def allocate_to_storage(incoming_l: float, capacity_l: float, current_l: float) -> float:
    if incoming_l < 0:
        raise ValueError("incoming_l cannot be negative")
    return min(incoming_l, available_storage_l(capacity_l, current_l))

