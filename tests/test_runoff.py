import pytest

from src.hydrology.runoff import runoff_volume_l


def test_runoff_volume_uses_millimetre_litre_identity():
    assert runoff_volume_l(10, 1_000, 0.8) == 8_000


@pytest.mark.parametrize(
    "rainfall,area,coefficient",
    [(-1, 100, 0.8), (1, -100, 0.8), (1, 100, 1.1)],
)
def test_runoff_rejects_invalid_inputs(rainfall, area, coefficient):
    with pytest.raises(ValueError):
        runoff_volume_l(rainfall, area, coefficient)

