import logging
from copy import deepcopy
from typing import cast

import numpy as np

from ..data_structures import (
    Data,
    Datapoint,
    Distribution,
    HeatPump,
    HeatPumps,
    Parameter,
    ParameterValueMinMax,
    ParameterValuePerlin,
    State,
    TimeBasedValue,
    Vary,
)
from .vary_perlin import create_perlin_field


def copy_parameter(state: State, parameter: Parameter) -> Data:
    """This function simply copies all values from a `Parameter` to a `Data` object without any transformation"""
    if isinstance(parameter.value, HeatPump):
        return vary_heatpump(state, parameter, False)
    return Data(name=parameter.name, value=deepcopy(parameter.value))


def vary_heatpump(state: State, parameter: Parameter, vary_location: bool) -> Data:
    resolution = state.general.cell_resolution
    number_cells = np.array(state.general.number_cells)

    hp = deepcopy(parameter.value)
    assert isinstance(hp, HeatPump)

    hp = handle_heatpump_values(state.get_rng(), hp)

    result_location = np.array(hp.location)
    if vary_location:
        # This is needed as we need to calculate the heatpump coordinates for pflotran.in
        result_location = (number_cells - 1) * state.get_rng().random(3) * resolution + (resolution * 0.5)

    return Data(
        name=parameter.name,
        value=HeatPump(
            location=result_location.tolist(), injection_temp=hp.injection_temp, injection_rate=hp.injection_rate
        ),
    )


def vary_parameter(state: State, parameter: Parameter, index: int) -> Data:
    """This function does the variation of `Parameter`s. It does so by implementing a large match-case that in turn
    invokes other functions that then work on the `Parameter.value` based on the `Parameter.vary` type.
    """
    assert not isinstance(parameter.value, HeatPumps)
    match parameter.vary:
        case Vary.FIXED:
            data = copy_parameter(state, parameter)
        case Vary.SPACE:
            if isinstance(parameter.value, ParameterValuePerlin):
                data = Data(
                    name=parameter.name,
                    value=create_perlin_field(state, parameter),
                )
            elif isinstance(parameter.value, float):
                raise ValueError(
                    f"Parameter {parameter.name} is vary.space and has a float value, "
                    f"it should be set to vary.fixed or vary.const with a min/max value instead; {parameter}"
                )
            # This should be inside the CONST block, yet it seems to make more sense to users to find it here
            elif isinstance(parameter.value, HeatPump):
                data = vary_heatpump(state, parameter, True)
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
                step_width = distance / (state.general.number_datapoints - 1)
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


def calculate_hp_coordinates(state: State) -> State:
    """Calculate the coordinates of each heatpump by multiplying with the cell_resolution"""

    for _, hp_data in state.heatpump_parameters.items():
        assert not isinstance(hp_data.value, HeatPumps)
        resolution = state.general.cell_resolution

        hp = hp_data.value
        assert isinstance(hp, HeatPump)

        # This is needed as we need to calculate the heatpump coordinates for pflotran.in
        result_location = (np.array(hp.location) - 1) * resolution + (resolution * 0.5)

        hp.location = result_location.tolist()

    return state


def handle_heatpump_values(rand: np.random.Generator, hp_data: HeatPump) -> HeatPump:
    """Normalize the given value to a `TimeBasedValue` with values that lay between the given min/max values."""

    assert isinstance(hp_data.injection_temp, TimeBasedValue)
    assert isinstance(hp_data.injection_rate, TimeBasedValue)

    for timestep, value in hp_data.injection_temp.values.items():
        # Iterate over each of the heat pumps time value
        if isinstance(value, ParameterValueMinMax):
            # Value is given as min/max
            hp_data.injection_temp.values[timestep] = value.max - (rand.random() * (value.max - value.min))

    for timestep, value in hp_data.injection_rate.values.items():
        # Iterate over each of the heat pumps time value
        if isinstance(value, ParameterValueMinMax):
            # Value is given as min/max
            hp_data.injection_rate.values[timestep] = value.max - (rand.random() * (value.max - value.min))

    return hp_data


def generate_heatpumps(state: State) -> State:
    """Generate `HeatPump`s from the given `HeatPumps` parameter. This function will remove all `HeatPumps` from
    `State.heatpump_parameters` and add `HeatPumps.number` `HeatPump`s to the dict. The `HeatPump.injection_temp` and
    `HeatPump.injection_rate` values are simply taken from a random number between the respective min and max values.
    """

    rand = state.get_rng()
    new_heatpumps: dict[str, Parameter] = {}
    for _, hps in state.heatpump_parameters.items():
        if isinstance(hps.value, HeatPump):
            new_heatpumps[hps.name] = hps
            continue

        if not isinstance(hps.value, HeatPumps):
            raise ValueError("There was a non HeatPumps item in heatpump_parameters")

        for index in range(hps.value.number):  # type:ignore
            name = f"{hps.name}_{index}"
            if (state.heatpump_parameters.get(name) is not None) and (new_heatpumps.get(name) is not None):
                msg = f"There is a naming clash for generated heatpump {name}"
                logging.error(msg)
                raise ValueError(msg)

            # XXX: This is actually always random
            location = np.ceil(rand.random(3) * cast(np.ndarray, state.general.number_cells)).tolist()

            injection_temp = hps.value.injection_temp
            injection_rate = hps.value.injection_rate

            logging.debug(
                "Generating heatpump with location %s, injection_temp %s, injection_rate %s",
                location,
                injection_temp,
                injection_rate,
            )
            new_heatpumps[name] = Parameter(
                name=name,
                vary=hps.vary,
                value=HeatPump(location=location, injection_temp=injection_temp, injection_rate=injection_rate),
            )

    for name, value in new_heatpumps.items():
        if isinstance(value, HeatPumps):
            raise ValueError(f"There should be no HeatPumps in the new_heatpumps dict, but {name} is.")

    logging.debug("Old heatpump_parameters: %s", state.heatpump_parameters)
    state.heatpump_parameters = new_heatpumps
    logging.debug("New heatpump_parameters: %s", state.heatpump_parameters)
    return state


def vary_params(state: State) -> State:
    """Calls the `vary_parameter` function for each datapoint sequentially."""

    for datapoint_index in range(state.general.number_datapoints):
        data = {}

        # This syntax merges the hydrogeological_parameters and the heatpump_parameters dicts so we don't have to write
        # two separate for loops
        for _, parameter in (state.hydrogeological_parameters | state.heatpump_parameters).items():
            parameter_data = vary_parameter(state, parameter, datapoint_index)
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        # TODO split into data_fixed etc
        state.datapoints.append(Datapoint(index=datapoint_index, data=data))

    if state.general.shuffle_datapoints:
        state = shuffle_datapoints(state)
        logging.debug("Shuffled datapoints")

    return state


def shuffle_datapoints(state: State) -> State:
    """Shuffles all `Parameter`s randomly in between the different `Datapoint`s. This is needed when e.g. two
    parameters are generated as `Vary.CONST` with `ParameterValueMinMax`, as otherwise they would both have min
    values in the first `Datapoint` and max values in the last one.
    """

    parameters: dict[str, list[Data]] = {}

    parameter_names = list(state.datapoints[0].data)
    for parameter in parameter_names:
        for datapoint in state.datapoints:
            param_list = parameters.get(parameter, [])
            param_list.append(datapoint.data[parameter])
            parameters[parameter] = param_list

        # This np.array -> shuffle -> array.tolist is necessary as, for some
        # reason, pyright doesn't get that list[Data] is an ArrayLike...
        array = parameters[parameter]
        array = np.array(array)
        state.get_rng().shuffle(array)
        parameters[parameter] = array.tolist()

    for parameter in parameter_names:
        for index in range(state.general.number_datapoints):
            state.datapoints[index].data[parameter] = parameters[parameter][index]

    return state


def handle_time_based_params(state: State) -> State:
    """Convert specific parameters to time based entries."""

    # Convert heatpumps to time based values
    for _, heatpump in state.heatpump_parameters.items():
        assert isinstance(heatpump.value, HeatPump)
        if not isinstance(heatpump.value.injection_temp, TimeBasedValue):
            heatpump.value.injection_temp = TimeBasedValue(values={0: heatpump.value.injection_temp})
        if not isinstance(heatpump.value.injection_rate, TimeBasedValue):
            heatpump.value.injection_rate = TimeBasedValue(values={0: heatpump.value.injection_rate})

    return state


def calculate_frequencies(state: State) -> State:
    """For every `Parameter` that has a value of `ParameterValuePerlin` type, calculate the frequency value if
    `ParameterValueMinMax` is given."""

    # Convert heatpumps to time based values
    for _, parameter in (state.hydrogeological_parameters | state.heatpump_parameters).items():
        if not isinstance(parameter.value, ParameterValuePerlin):
            continue

        if not isinstance(parameter.value.frequency, ParameterValueMinMax):
            continue

        rand = state.get_rng()

        min = parameter.value.frequency.min
        max = parameter.value.frequency.max

        val1 = max - (rand.random() * (max - min))
        val2 = max - (rand.random() * (max - min))
        val3 = max - (rand.random() * (max - min))

        parameter.value.frequency = [val1, val2, val3]

    return state
