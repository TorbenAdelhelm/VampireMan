import pytest

from vampireman.data_structures import (
    HeatPump,
    HeatPumps,
    Parameter,
    State,
    ValueMinMax,
    ValueTimeSeries,
    Vary,
)
from vampireman.pipeline import preparation_stage


def test_prepare_heatpump():
    state = State()
    state.general.cell_resolution = 1.0
    state.heatpump_parameters = {
        "hp1": Parameter(
            name="hp1",
            vary=Vary.FIXED,
            value=HeatPump(location=[16, 32, 1], injection_temp=10.5, injection_rate=0.002),
        )
    }

    state = preparation_stage(state)

    assert state.heatpump_parameters.get("hp1").value.location == [15.5, 31.5, 0.5]

    state = State()
    state.heatpump_parameters = {
        "hp1": Parameter(
            name="hp1",
            vary=Vary.FIXED,
            value=HeatPump(location=[16, 32, 1], injection_temp=10.5, injection_rate=0.002),
        )
    }

    state = preparation_stage(state)

    assert state.heatpump_parameters.get("hp1").value.location == [77.5, 157.5, 2.5]


def test_prepare_heatpump_generation():
    state = State()
    state.heatpump_parameters = {
        "hps": Parameter(
            name="hps",
            vary=Vary.FIXED,
            value=HeatPumps(
                number=10,
                injection_temp=ValueMinMax(min=14, max=18),
                injection_rate=ValueTimeSeries(
                    time_unit="year",
                    values={
                        0: ValueMinMax(min=0, max=0.002),
                        1: 0,
                        2: ValueMinMax(min=0.00024, max=0.002),
                    },
                ),
            ),
        )
    }
    state = preparation_stage(state)
    assert len(state.heatpump_parameters) == 10
    assert state.heatpump_parameters.get("hps_0").value.location == [102.5, 347.5, 2.5]
    assert state.heatpump_parameters.get("hps_9").value.location == [157.5, 877.5, 2.5]
    assert len(state.heatpump_parameters.get("hps_9").value.injection_temp.values) == 1
    assert len(state.heatpump_parameters.get("hps_8").value.injection_rate.values) == 3


def test_prepare_heatpump_name_clash():
    state = State()
    state.heatpump_parameters = {
        "hp_0": Parameter(
            name="hp_0",
            vary=Vary.FIXED,
            value=HeatPump(location=[16, 32, 1], injection_temp=10.5, injection_rate=0.002),
        ),
        "hp": Parameter(
            name="hp",
            vary=Vary.FIXED,
            value=HeatPumps(
                number=1,
                injection_temp=ValueMinMax(min=1, max=2),
                injection_rate=ValueMinMax(min=1, max=2),
            ),
        ),
    }

    with pytest.raises(ValueError):
        preparation_stage(state)
