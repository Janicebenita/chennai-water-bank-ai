"""Deterministic rainfall profiles for reliable live demonstrations."""

from __future__ import annotations


CHENNAI_STORM_PROFILE_MM_HR: tuple[float, ...] = (
    8.0,
    22.0,
    48.0,
    82.0,
    108.0,
    76.0,
    42.0,
    18.0,
)


def rainfall_depth_for_interval(intensity_mm_hr: float, interval_minutes: float) -> float:
    if intensity_mm_hr < 0 or interval_minutes < 0:
        raise ValueError("rainfall intensity and interval cannot be negative")
    return intensity_mm_hr * interval_minutes / 60.0

