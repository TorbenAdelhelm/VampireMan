import logging

import numpy as np

from ..config import (
    Config,
    Data,
    Datapoint,
    HeatPump,
    HeatPumps,
    Parameter,
    ParameterValueMinMax,
    ParameterValuePerlin,
    Vary,
)
from .vary_perlin import create_const_field, create_vary_field


def copy_parameter(parameter: Parameter) -> Data:
    """This function simply copies all values from a `Parameter` to a `Data` object without any transformation"""
    return Data(name=parameter.name, value=parameter.value)


def vary_heatpump(config: Config, parameter: Parameter) -> Data:
    resolution = np.array(config.general.cell_resolution)
    number_cells = np.array(config.general.number_cells)

    hp = parameter.value
    assert isinstance(hp, HeatPump)

    # This is needed as we need to calculate the heatpump coordinates for pflotran.in
    result_location = (number_cells - 1) * config.get_rng().random(3) * resolution + (resolution * 0.5)

    return Data(
        name=parameter.name,
        value=HeatPump(
            location=result_location.tolist(), injection_temp=hp.injection_temp, injection_rate=hp.injection_rate
        ),
    )


def vary_parameter(config: Config, parameter: Parameter, index: int) -> Data | None:
    data = None
    assert not isinstance(parameter.value, HeatPumps)
    match parameter.vary:
        case Vary.FIXED:
            data = copy_parameter(parameter)
        case Vary.SPACE:
            if isinstance(parameter.value, ParameterValuePerlin):
                data = Data(
                    name=parameter.name,
                    value=create_vary_field(config, parameter),
                )
            elif isinstance(parameter.value, float):
                data = Data(
                    name=parameter.name,
                    value=create_const_field(config, parameter.value),
                )
            elif isinstance(parameter.value, HeatPump):
                data = vary_heatpump(config, parameter)
            elif isinstance(parameter.value, ParameterValueMinMax):
                raise ValueError(
                    f"Parameter {parameter.name} is vary.space and has min/max values, "
                    f"it should be set to vary.perlin instead; {parameter}"
                )
            else:
                raise NotImplementedError(f"Dont know how to vary {parameter}")

        # TODO make this less copy paste
        case Vary.CONST:
            if isinstance(parameter.value, ParameterValueMinMax):
                # XXX: This will generate one float per datapoint, between min and max values
                # Currently, there is no shuffling implemented
                # XXX: somehow, the values are not reaching the max value
                distance = parameter.value.max - parameter.value.min
                step_width = distance / (config.general.number_datapoints + 1)
                value = parameter.value.min + step_width * index
                data = Data(
                    name=parameter.name,
                    value=value,
                )
            else:
                logging.error(
                    "No implementation for %s and %s in parameter %s",
                    type(parameter.value),
                    parameter.vary,
                    parameter.name,
                )
                raise NotImplementedError()
        case _:
            raise ValueError()
    return data


def calculate_hp_coordinates(config: Config) -> Config:
    """Calculate the coordinates of each heatpump by multiplying with the cell_resolution"""

    for _, hp_data in config.heatpump_parameters.items():
        assert not isinstance(hp_data.value, HeatPumps)
        resolution = np.array(config.general.cell_resolution)

        hp = hp_data.value
        assert isinstance(hp, HeatPump)

        # This is needed as we need to calculate the heatpump coordinates for pflotran.in
        result_location = (np.array(hp.location) - 1) * resolution + (resolution * 0.5)

        hp.location = result_location.tolist()

    return config


def generate_heatpumps(config: Config):
    rand = config.get_rng()
    new_heatpumps: dict[str, Parameter] = {}
    for _, hps in config.heatpump_parameters.items():
        if isinstance(hps.value, HeatPump):
            new_heatpumps[hps.name] = hps
            continue

        if not isinstance(hps.value, HeatPumps):
            raise ValueError()

        # TODO: calculate relevant parameters
        for index in range(hps.value.number):  # type:ignore
            injection_temp_min = hps.value.injection_temp_min
            injection_temp_max = hps.value.injection_temp_max
            injection_rate_min = hps.value.injection_rate_min
            injection_rate_max = hps.value.injection_rate_max

            location = np.ceil(rand.random(3) * config.general.number_cells).tolist()
            injection_temp = injection_temp_max - (rand.random() * (injection_temp_max - injection_temp_min))
            injection_rate = injection_rate_max - (rand.random() * (injection_rate_max - injection_rate_min))
            logging.debug(
                "Generating heatpump with location %s, injection_temp %s, injection_rate %s",
                location,
                injection_temp,
                injection_rate,
            )
            name = f"{hps.name}_{index}"
            if (config.heatpump_parameters.get(name) is not None) and (new_heatpumps.get(name) is not None):
                # TODO write test for this
                msg = f"There is a naming clash for generated heatpump {name}"
                logging.error(msg)
                raise ValueError(msg)
            new_heatpumps[name] = Parameter(
                name=name,
                vary=hps.vary,
                value=HeatPump(location=location, injection_temp=injection_temp, injection_rate=injection_rate),
            )

    for name, value in new_heatpumps.items():
        if isinstance(value, HeatPumps):
            raise ValueError(f"There should be no HeatPumps in the new_heatpumps dict, but {name} is.")

    config.heatpump_parameters = new_heatpumps
    return config


def vary_params(config: Config) -> Config:
    # for step in config.steps:
    #     filter over params where step == param.step
    for datapoint_index in range(config.general.number_datapoints):
        data = {}

        for _, parameter in config.hydrogeological_parameters.items():
            parameter_data = vary_parameter(config, parameter, datapoint_index)
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        for _, parameter in config.heatpump_parameters.items():
            parameter_data = vary_parameter(config, parameter, datapoint_index)
            if parameter_data is None:
                continue
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        # TODO: do we need to shuffle the datapoints for each parameter here?
        # TODO split into data_fixed etc
        config.datapoints.append(Datapoint(index=datapoint_index, data=data))

    return config
