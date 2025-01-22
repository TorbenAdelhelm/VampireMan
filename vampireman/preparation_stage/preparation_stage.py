"""The preparation stage is responsible for reading in any supplementary files specified in any of the
`vampireman.data_structures.Parameter.value` fields.

Afterwards, for each `vampireman.data_structures.HeatPumps` parameter, the corresponding
`vampireman.data_structures.HeatPump`s are generated and added to the
`vampireman.data_structures.State.heatpump_parameters` dict. The `vampireman.data_structures.HeatPumps` are then dropped
from the state.

`vampireman.data_structures.HeatPump.location` are multiplied with
`vampireman.data_structures.GeneralConfig.cell_resolution` to change the cell based representation to a coordinate based
representation.

As a last step, the `vampireman.data_structures.HeatPump.injection_temp` and
`vampireman.data_structures.HeatPump.injection_rate` values are converted to
`vampireman.data_structures.ValueTimeSeries` values so they can be handled in a uniform way later.
"""
import logging
from typing import cast

import numpy as np

from ..data_structures import HeatPump, HeatPumps, Parameter, State, ValueTimeSeries
from ..utils import create_dataset_and_datapoint_dirs, profile_function, read_in_files
from ..validation_stage.validation_stage import are_duplicate_locations_in_heatpumps
from ..variation_stage.vary import generate_heatpump_location


@profile_function
def preparation_stage(state: State) -> State:
    create_dataset_and_datapoint_dirs(state)
    state = read_in_files(state)
    state = generate_heatpumps(state)
    state = calculate_hp_coordinates(state)
    state = handle_time_based_params(state)
    return state


def handle_time_based_params(state: State) -> State:
    """Convert specific parameters to time based entries."""

    # Convert heatpumps to time based values
    for _, heatpump in state.heatpump_parameters.items():
        assert isinstance(heatpump.value, HeatPump)
        if not isinstance(heatpump.value.injection_temp, ValueTimeSeries):
            heatpump.value.injection_temp = ValueTimeSeries(values={0: heatpump.value.injection_temp})
        if not isinstance(heatpump.value.injection_rate, ValueTimeSeries):
            heatpump.value.injection_rate = ValueTimeSeries(values={0: heatpump.value.injection_rate})

    return state


def calculate_hp_coordinates(state: State) -> State:
    """Calculate the coordinates of each heatpump by multiplying with the cell_resolution"""

    for _, hp_data in state.heatpump_parameters.items():
        assert isinstance(hp_data.value, HeatPump)
        if hp_data.value.location is None:
            # This means the heatpump is assigned a random location during vary stage anyway
            continue

        resolution = state.general.cell_resolution

        hp = hp_data.value
        assert isinstance(hp, HeatPump)

        # This is needed as we need to calculate the heatpump coordinates for pflotran.in
        result_location = (np.array(hp.location) - 1) * resolution + (resolution * 0.5)

        hp.location = cast(list[float], result_location.tolist())

    return state


def generate_heatpumps(state: State) -> State:
    """Generate `HeatPump`s from the given `HeatPumps` parameter. This function will remove all `HeatPumps` from
    `State.heatpump_parameters` and add `HeatPumps.number` `HeatPump`s to the dict. The `HeatPump.injection_temp` and
    `HeatPump.injection_rate` values are simply taken from a random number between the respective min and max values.
    """

    new_heatpumps: dict[str, Parameter] = {}

    # Need to get the explicit heatpumps first, in case of location clashes we can simply draw another random number
    for _, hps in state.heatpump_parameters.items():
        if isinstance(hps.value, HeatPump):
            new_heatpumps[hps.name] = hps
            continue

    for _, hps in state.heatpump_parameters.items():
        if isinstance(hps.value, HeatPump):
            continue

        if not isinstance(hps.value, HeatPumps):
            raise ValueError("There was a non HeatPumps item in heatpump_parameters")

        for index in range(hps.value.number):  # type:ignore
            name = f"{hps.name}_{index}"
            if (state.heatpump_parameters.get(name) is not None) and (new_heatpumps.get(name) is not None):
                msg = f"There is a naming clash for generated heatpump {name}"
                logging.error(msg)
                raise ValueError(msg)

            injection_temp = hps.value.injection_temp
            injection_rate = hps.value.injection_rate

            location = generate_heatpump_location(state)

            heatpump = HeatPump(
                location=cast(list[float], location),
                injection_temp=injection_temp,
                injection_rate=injection_rate,
            )
            logging.debug("Generated HeatPump %s", heatpump)

            heatpumps = cast(list[HeatPump], [param.value for _, param in new_heatpumps.items()])
            heatpumps.append(heatpump)
            while are_duplicate_locations_in_heatpumps(heatpumps):
                # Generate new heatpump location if the one we had is already taken
                # TODO write test for this
                heatpump.location = generate_heatpump_location(state)

            new_heatpumps[name] = Parameter(
                name=name,
                vary=hps.vary,
                value=heatpump,
            )

    for name, value in new_heatpumps.items():
        if isinstance(value, HeatPumps):
            raise ValueError(f"There should be no HeatPumps in the new_heatpumps dict, but {name} is.")

    logging.debug("Old heatpump_parameters: %s", state.heatpump_parameters)
    state.heatpump_parameters = new_heatpumps
    logging.debug("New heatpump_parameters: %s", state.heatpump_parameters)
    return state
