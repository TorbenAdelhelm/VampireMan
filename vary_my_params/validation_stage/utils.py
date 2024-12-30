import logging

from ..data_structures import HeatPump, HeatPumps, State
from ..utils import profile_function


@profile_function
def validation_stage(state: State) -> State:
    # TODO make this more extensive
    # XXX this could also be done by pydantic...

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
    heatpumps = [{name: d.name} for name, d in state.heatpump_parameters.items() if isinstance(d.value, HeatPump)]
    heatpumps_gen = [{name: d.name} for name, d in state.heatpump_parameters.items() if isinstance(d.value, HeatPumps)]
    if len(heatpumps) + len(heatpumps_gen) < 1:
        logging.error("There are no heatpumps in this simulation. This usually doesn't make much sense.")

    logging.info("State is valid")
    return state
