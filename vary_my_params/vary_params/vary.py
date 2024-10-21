import logging
from copy import deepcopy

import numpy as np

from ..config import (
    Config,
    Data,
    Datapoint,
    Distribution,
    HeatPump,
    HeatPumps,
    Parameter,
    ParameterValueMinMax,
    ParameterValuePerlin,
    Vary,
)
from .vary_perlin import create_perlin_field


def copy_parameter(parameter: Parameter) -> Data:
    """This function simply copies all values from a `Parameter` to a `Data` object without any transformation"""
    return Data(name=parameter.name, value=deepcopy(parameter.value))


def vary_heatpump(config: Config, parameter: Parameter) -> Data:
    resolution = np.array(config.general.cell_resolution)
    number_cells = np.array(config.general.number_cells)

    hp = deepcopy(parameter.value)
    assert isinstance(hp, HeatPump)

    # This is needed as we need to calculate the heatpump coordinates for pflotran.in
    result_location = (number_cells - 1) * config.get_rng().random(3) * resolution + (resolution * 0.5)

    return Data(
        name=parameter.name,
        value=HeatPump(
            location=result_location.tolist(), injection_temp=hp.injection_temp, injection_rate=hp.injection_rate
        ),
    )


def vary_parameter(config: Config, parameter: Parameter, index: int) -> Data:
    """This function does the variation of `Parameter`s. It does so by implementing a large match-case that in turn
    invokes other functions that then work on the `Parameter.value` based on the `Parameter.vary` type.
    """
    assert not isinstance(parameter.value, HeatPumps)
    match parameter.vary:
        case Vary.FIXED:
            data = copy_parameter(parameter)
        case Vary.SPACE:
            if isinstance(parameter.value, ParameterValuePerlin):
                data = Data(
                    name=parameter.name,
                    value=create_perlin_field(config, parameter),
                )
            elif isinstance(parameter.value, float):
                raise ValueError(
                    f"Parameter {parameter.name} is vary.space and has a float value, "
                    f"it should be set to vary.fixed or vary.const with a min/max value instead; {parameter}"
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

        case Vary.CONST:
            if isinstance(parameter.value, ParameterValueMinMax):
                # XXX: This will generate one float per datapoint, between min and max values
                # Currently, there is no shuffling implemented
                max = deepcopy(parameter.value.max)
                min = deepcopy(parameter.value.min)

                if parameter.distribution == Distribution.LOG:
                    max = np.log10(max)
                    min = np.log10(min)

                distance = max - min
                step_width = distance / (config.general.number_datapoints - 1)
                value = min + step_width * index

                if parameter.distribution == Distribution.LOG:
                    value = 10**value

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


def generate_heatpumps(config: Config) -> Config:
    """Generate `HeatPump`s from the given `HeatPumps` parameter. This function will remove all `HeatPumps` from
    `Config.heatpump_parameters` and add `HeatPumps.number` `HeatPump`s to the dict. The `HeatPump.injection_temp` and
    `HeatPump.injection_rate` values are simply taken from a random number between the respective min and max values.
    """

    rand = config.get_rng()
    new_heatpumps: dict[str, Parameter] = {}
    for _, hps in config.heatpump_parameters.items():
        if isinstance(hps.value, HeatPump):
            new_heatpumps[hps.name] = hps
            continue

        if not isinstance(hps.value, HeatPumps):
            raise ValueError("There was a non HeatPumps item in heatpump_parameters")

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

    logging.debug("Old heatpump_parameters: %s", config.heatpump_parameters)
    config.heatpump_parameters = new_heatpumps
    logging.debug("New heatpump_parameters: %s", config.heatpump_parameters)
    return config


def vary_params(config: Config) -> Config:
    """Calls the `vary_parameter` function for each datapoint sequentially."""

    # for step in config.steps:
    #     filter over params where step == param.step
    for datapoint_index in range(config.general.number_datapoints):
        data = {}

        # This syntax merges the hydrogeological_parameters and the heatpump_parameters dicts so we don't have to write
        # two separate for loops
        for _, parameter in (config.hydrogeological_parameters | config.heatpump_parameters).items():
            parameter_data = vary_parameter(config, parameter, datapoint_index)
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        # TODO split into data_fixed etc
        config.datapoints.append(Datapoint(index=datapoint_index, data=data))

    if config.general.shuffle_datapoints:
        config = shuffle_datapoints(config)
        logging.debug("Shuffled datapoints")

    return config


def shuffle_datapoints(config: Config) -> Config:
    """Shuffles all `Parameter`s randomly in between the different `Datapoint`s. This is needed when e.g. two
    parameters are generated as `Vary.CONST` with `ParameterValueMinMax`, as otherwise they would both have min
    values in the first `Datapoint` and max values in the last one.
    """

    parameters: dict[str, list[Data]] = {}

    parameter_names = list(config.datapoints[0].data)
    for parameter in parameter_names:
        for datapoint in config.datapoints:
            param_list = parameters.get(parameter, [])
            param_list.append(datapoint.data[parameter])
            parameters[parameter] = param_list

        # This np.array -> shuffle -> array.tolist is necessary as, for some
        # reason, pyright doesn't get that list[Data] is an ArrayLike...
        array = parameters[parameter]
        array = np.array(array)
        config.get_rng().shuffle(array)
        parameters[parameter] = array.tolist()

    for parameter in parameter_names:
        for index in range(config.general.number_datapoints):
            config.datapoints[index].data[parameter] = parameters[parameter][index]

    return config
