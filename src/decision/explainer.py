"""Human-facing formula and scoring descriptions."""

METHODOLOGY = {
    "runoff": "runoff_litres = rainfall_mm × catchment_area_m² × runoff_coefficient",
    "storage": "available_storage_l = storage_capacity_l − current_storage_l",
    "recharge": (
        "eligible_recharge_l = capacity_l_per_hour × interval_hours × "
        "(1 − soil_saturation / saturation_block_threshold)"
    ),
    "retained": "retained_l = stored_l + recharged_l",
    "downstream": "immediate_downstream_l = diverted_l + controlled_discharge_l",
}

SCORE_FORMULAS = {
    "storage": (
        "0.45 × usable tank capacity + 0.35 × drain stress + 0.20 × tank headroom"
    ),
    "recharge": (
        "0.40 × eligible recharge capacity + 0.25 × unsaturated soil + "
        "0.20 × drain stress + 0.15 × tank pressure"
    ),
    "discharge": (
        "0.45 × capacity pressure + 0.35 × soil saturation + 0.20 × drain stress"
    ),
}

