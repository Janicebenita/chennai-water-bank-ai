from src.hydrology.storage import allocate_to_storage, available_storage_l


def test_storage_cannot_exceed_capacity():
    assert allocate_to_storage(8_000, capacity_l=10_000, current_l=7_000) == 3_000


def test_available_storage_never_negative():
    assert available_storage_l(10_000, 12_000) == 0

