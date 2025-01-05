import logging

from ..data_structures import HeatPump, HeatPumps, State
from ..utils import profile_function


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
    heatpumps = [
        {name: d.name} for name, d in state.heatpump_parameters.items() if isinstance(d.value, HeatPump | HeatPumps)
    ]
    if len(heatpumps) < 1:
        logging.error("There are no heatpumps in this simulation. This usually doesn't make much sense.")
        # TODO: Should we raise here?

    heatpumps_in_hydrogeological_parameters = [
        {name: d.name}
        for name, d in state.hydrogeological_parameters.items()
        if isinstance(d.value, HeatPump | HeatPumps)
    ]
    if len(heatpumps_in_hydrogeological_parameters) > 0:
        raise ValueError("Heat pumps found in hydrogeological_parameters, this is not allowed")

    logging.info("State is valid")
    return state
