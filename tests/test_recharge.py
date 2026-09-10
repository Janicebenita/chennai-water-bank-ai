from src.hydrology.recharge import recharge_available_l


def test_recharge_is_limited_by_interval_and_soil_factor():
    result = recharge_available_l(
        12_000,
        30,
        enabled=True,
        quality_allowed=True,
        first_flush_active=False,
        soil_saturation_percent=42.5,
        saturation_block_percent=85,
    )
    assert result == 3_000


def test_first_flush_blocks_recharge():
    assert (
        recharge_available_l(
            12_000,
            60,
            enabled=True,
            quality_allowed=True,
            first_flush_active=True,
            soil_saturation_percent=10,
        )
        == 0
    )


def test_saturated_soil_blocks_recharge():
    assert (
        recharge_available_l(
            12_000,
            60,
            enabled=True,
            quality_allowed=True,
            first_flush_active=False,
            soil_saturation_percent=90,
        )
        == 0
    )

