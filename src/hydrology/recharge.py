"""Estimated prototype recharge capacity."""


def recharge_available_l(
    capacity_l_per_hour: float,
    interval_minutes: float,
    *,
    enabled: bool,
    quality_allowed: bool,
    first_flush_active: bool,
    soil_saturation_percent: float,
    saturation_block_percent: float = 85.0,
) -> float:
    """Return eligible recharge volume for an interval.

    This is a capacity screen, not site-specific hydrogeological proof.
    """
    if capacity_l_per_hour < 0 or interval_minutes < 0:
        raise ValueError("recharge capacity and interval cannot be negative")
    if (
        not enabled
        or not quality_allowed
        or first_flush_active
        or soil_saturation_percent >= saturation_block_percent
    ):
        return 0.0
    soil_factor = max(0.0, 1.0 - soil_saturation_percent / saturation_block_percent)
    return capacity_l_per_hour * (interval_minutes / 60.0) * soil_factor

