"""Simplified runoff-volume calculation."""


def runoff_volume_l(
    rainfall_mm: float, catchment_area_m2: float, runoff_coefficient: float
) -> float:
    """Calculate litres of runoff using 1 mm over 1 m² = 1 litre."""
    if rainfall_mm < 0:
        raise ValueError("rainfall_mm cannot be negative")
    if catchment_area_m2 < 0:
        raise ValueError("catchment_area_m2 cannot be negative")
    if not 0 <= runoff_coefficient <= 1:
        raise ValueError("runoff_coefficient must be between 0 and 1")
    return rainfall_mm * catchment_area_m2 * runoff_coefficient

