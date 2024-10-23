import numpy as np

from vary_my_params.config import (
    Config,
    Distribution,
    HeatPump,
    Parameter,
    ParameterValueMinMax,
    ParameterValuePerlin,
    TimeBasedValue,
    Vary,
)
from vary_my_params.pipeline import prepare_parameters, run_vary_params
from vary_my_params.utils import create_dataset_and_datapoint_dirs


def test_vary_copy():
    config = Config()
    config.general.interactive = False

    create_dataset_and_datapoint_dirs(config)

    config.heatpump_parameters["hp1"] = Parameter(
        name="hp1",
        vary=Vary.FIXED,
        value=HeatPump(location=[16, 32, 1], injection_temp=13.6, injection_rate=0.00024),
    )

    temp_param = config.hydrogeological_parameters.get("temperature")
    hp_param = config.heatpump_parameters.get("hp1")

    assert len(config.datapoints) == 0
    config = prepare_parameters(config)
    config = run_vary_params(config)
    assert len(config.datapoints) == 1

    temp_data = config.datapoints[0].data.get("temperature")
    hp_data = config.datapoints[0].data.get("hp1")

    assert temp_param != temp_data
    assert temp_param.value == temp_data.value

    # Parameter value shouldn't change
    temp_data.value *= 6
    assert temp_param.value != temp_data.value

    assert hp_data.value.location == hp_param.value.location

    hp_data.value.location[0] = 123
    assert hp_data.value.location != hp_param.value.location


def test_vary_space():
    config = Config()
    config.general.interactive = False
    config.general.number_datapoints = 2

    create_dataset_and_datapoint_dirs(config)

    config.hydrogeological_parameters["param_scalar"] = Parameter(
        name="param_scalar",
        vary=Vary.FIXED,
        value=1,
    )
    config.hydrogeological_parameters["param_perlin"] = Parameter(
        name="param_perlin",
        vary=Vary.SPACE,
        distribution=Distribution.LOG,
        value=ParameterValuePerlin(frequency=[18, 18, 18], max=2, min=1),
    )

    param_scalar = config.hydrogeological_parameters.get("param_scalar")

    assert len(config.datapoints) == 0
    config = run_vary_params(config)
    assert len(config.datapoints) == 2

    data_scalar_0 = config.datapoints[0].data.get("param_scalar")
    data_scalar_1 = config.datapoints[1].data.get("param_scalar")

    data_perlin_0 = config.datapoints[0].data.get("param_perlin")
    data_perlin_1 = config.datapoints[1].data.get("param_perlin")

    # Should be equal across dataset
    assert data_scalar_0.value == data_scalar_1.value
    assert param_scalar.value == data_scalar_0.value

    # TODO: Write a better test
    assert not np.array_equal(data_perlin_0.value, data_perlin_1.value)


def test_vary_heatpump():
    config = Config()
    config.general.interactive = False
    config.general.number_datapoints = 2

    create_dataset_and_datapoint_dirs(config)

    config.heatpump_parameters["hp1"] = Parameter(
        name="hp1",
        vary=Vary.SPACE,
        value=HeatPump(location=[16, 32, 1], injection_temp=13.6, injection_rate=0.00024),
    )

    hp_param = config.heatpump_parameters.get("hp1")

    assert len(config.datapoints) == 0
    config = prepare_parameters(config)
    config = run_vary_params(config)
    assert len(config.datapoints) == 2

    hp_data_0 = config.datapoints[0].data.get("hp1")
    hp_data_1 = config.datapoints[1].data.get("hp1")

    # XXX: These tests could be improved
    assert hp_data_0.value.location != hp_param.value.location
    assert hp_data_0.value.location != hp_data_1.value.location


def test_vary_const():
    # TODO: Write CONST&&ParameterValueMinMaxArray test
    config = Config()
    config.general.interactive = False
    config.general.number_datapoints = 3

    create_dataset_and_datapoint_dirs(config)

    config.hydrogeological_parameters["parameter"] = Parameter(
        name="parameter",
        vary=Vary.CONST,
        value=ParameterValueMinMax(min=1, max=5),
    )
    config.hydrogeological_parameters["parameter2"] = Parameter(
        name="parameter2",
        vary=Vary.CONST,
        value=ParameterValueMinMax(min=-0.12, max=0.32),
    )

    param = config.hydrogeological_parameters.get("parameter")

    assert len(config.datapoints) == 0
    config = run_vary_params(config)
    assert len(config.datapoints) == 3

    data_0 = config.datapoints[0].data.get("parameter")
    data_1 = config.datapoints[1].data.get("parameter")
    data_2 = config.datapoints[2].data.get("parameter")

    assert data_0.value == param.value.min
    assert data_1.value == 3
    assert data_2.value == param.value.max

    data_0 = config.datapoints[0].data.get("parameter2")
    data_1 = config.datapoints[1].data.get("parameter2")
    data_2 = config.datapoints[2].data.get("parameter2")

    assert data_0.value == -0.12
    assert data_1.value == 0.1
    assert data_2.value == 0.32


def test_time_based_conversion():
    config = Config()

    config.heatpump_parameters = {
        "hp1": Parameter(
            name="hp1",
            value=HeatPump(location=[1, 1, 1], injection_temp=10, injection_rate=0.01),
        )
    }

    assert config.heatpump_parameters.get("hp1").value.injection_temp == 10
    config = prepare_parameters(config)
    assert config.heatpump_parameters.get("hp1").value.injection_temp.values.get(0) == 10


def test_time_based_provided_values():
    config = Config()

    config.heatpump_parameters = {
        "hp1": Parameter(
            name="hp1",
            value=HeatPump(
                location=[1, 1, 1],
                injection_temp=TimeBasedValue(
                    values={
                        0: 0,
                        1: 1,
                        2: 2,
                        3: 3,
                        4: 4,
                    }
                ),
                injection_rate=0.01,
            ),
        )
    }

    config = prepare_parameters(config)
    for i in range(2):
        assert config.heatpump_parameters.get("hp1").value.injection_temp.values.get(i) == i


def test_time_based_config():
    config = Config(
        **{
            "general": {
                "interactive": False,
            },
            "heatpump_parameters": {
                "hp1": {
                    "name": "hp1",
                    "value": {
                        "location": [1, 1, 1],
                        "injection_temp": {
                            "time_unit": "day",
                            "values": {
                                1: 1,
                            },
                        },
                        "injection_rate": 0.001,
                    },
                }
            },
        }
    )

    config = prepare_parameters(config)
    assert config.heatpump_parameters.get("hp1").value.injection_temp.values.get(1) == 1
