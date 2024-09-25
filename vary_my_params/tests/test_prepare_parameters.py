from vary_my_params.config import Config, HeatPump, HeatPumps, Parameter, Vary
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
                injection_temp_min=1,
                injection_temp_max=2,
                injection_rate_min=2,
                injection_rate_max=2,
            ),
        )
    }
    config = prepare_parameters(config)
    assert len(config.heatpump_parameters) == 10
    assert config.heatpump_parameters.get("hps_0").value.location == [102.5, 172.5, 2.5]
    assert config.heatpump_parameters.get("hps_9").value.location == [142.5, 147.5, 2.5]
