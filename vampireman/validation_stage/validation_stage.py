import logging

from ..data_structures import HeatPump, HeatPumps, State
from ..utils import profile_function, write_data_to_verified_json_file


@profile_function
def validation_stage(state: State) -> State:
    pressure_gradient = state.hydrogeological_parameters.get("pressure_gradient")
    permeability = state.hydrogeological_parameters.get("permeability")
    temperature = state.hydrogeological_parameters.get("temperature")

    if permeability is None:
        raise ValueError("`permeability` must not be None")
    if pressure_gradient is None:
        raise ValueError("`pressure_gradient` must not be None")
    if temperature is None:
        raise ValueError("`temperature` must not be None")

    # Simulation without heatpumps doesn't make much sense
    heatpumps = [d.value for name, d in state.heatpump_parameters.items() if isinstance(d.value, HeatPump)]
    if len(heatpumps) < 1:
        logging.error("There are no heatpumps in this simulation. This usually doesn't make much sense.")
        # XXX: Should we raise here?

    if are_duplicate_locations_in_heatpumps(heatpumps):
        raise ValueError("Duplicate HeatPump location detected!")

    heatpumps_in_hydrogeological_parameters = [
        d.value for name, d in state.hydrogeological_parameters.items() if isinstance(d.value, HeatPump | HeatPumps)
    ]
    if len(heatpumps_in_hydrogeological_parameters) > 0:
        raise ValueError("Heat pumps found in hydrogeological_parameters, this is not allowed")

    logging.info("State is valid")
    write_data_to_verified_json_file(state, state.general.output_directory / "state.json", state)

    return state


def are_duplicate_locations_in_heatpumps(heatpumps: list[HeatPump]) -> bool:
    """Check that no heatpumps have the same location."""
    # TODO write test for this
    heatpump_locations = set()
    duplicates_detected = False

    for heatpump in heatpumps:
        # Needed as lists are not hashable
        location = heatpump.location
        if location is None:
            # This means, the heatpump is varied spatially later on while ensuring the location is unique.
            continue

        location = (location[0], location[1], location[2])

        if location in heatpump_locations:
            duplicates_detected = True
        else:
            heatpump_locations.add(location)

    return duplicates_detected
