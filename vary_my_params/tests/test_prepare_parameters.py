import pytest

from vary_my_params.config import Config, HeatPump, HeatPumps, Parameter, ParameterValueMinMax, TimeBasedValue, Vary
from vary_my_params.pipeline import prepare_parameters


def test_prepare_heatpump():
    config = Config()
    config.general.cell_resolution = [1, 1, 1]
    config.heatpump_parameters = {
        "hp1": Parameter(
            name="hp1",
            vary=Vary.FIXED,
            value=HeatPump(location=[16, 32, 1], injection_temp=10.5, injection_rate=0.002),
        )
    }

    config = prepare_parameters(config)

    assert config.heatpump_parameters.get("hp1").value.location == [15.5, 31.5, 0.5]

    config = Config()
    config.heatpump_parameters = {
        "hp1": Parameter(
            name="hp1",
            vary=Vary.FIXED,
            value=HeatPump(location=[16, 32, 1], injection_temp=10.5, injection_rate=0.002),
        )
    }

    config = prepare_parameters(config)

    assert config.heatpump_parameters.get("hp1").value.location == [77.5, 157.5, 2.5]


def test_prepare_heatpump_generation():
    config = Config()
    config.heatpump_parameters = {
        "hps": Parameter(
            name="hps",
            vary=Vary.FIXED,
            value=HeatPumps(
                number=10,
                injection_temp=ParameterValueMinMax(min=14, max=18),
                injection_rate=TimeBasedValue(
                    time_unit="year",
                    values={
                        0: ParameterValueMinMax(min=0, max=0.002),
                        1: 0,
                        2: ParameterValueMinMax(min=0.00024, max=0.002),
                    },
                ),
            ),
        )
    }
    config = prepare_parameters(config)
    assert len(config.heatpump_parameters) == 10
    assert config.heatpump_parameters.get("hps_0").value.location == [102.5, 347.5, 2.5]
    assert config.heatpump_parameters.get("hps_9").value.location == [52.5, 192.5, 2.5]
    assert config.heatpump_parameters.get("hps_9").value.injection_temp.values[0] == 14.814702918850823
    assert config.heatpump_parameters.get("hps_9").value.injection_rate.values[1] == 0


def test_prepare_heatpump_name_clash():
    config = Config()
    config.heatpump_parameters = {
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
                injection_temp=ParameterValueMinMax(min=1, max=2),
                injection_rate=ParameterValueMinMax(min=1, max=2),
            ),
        ),
    }

    with pytest.raises(ValueError):
        prepare_parameters(config)
