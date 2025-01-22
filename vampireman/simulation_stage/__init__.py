"""The simulation stage..."""

from ..data_structures import State
from ..utils import get_sim_tool_implementation, profile_function


@profile_function
def simulation_stage(state: State):
    """This function runs the simulation tool specific stage based on the
    `vampireman.data_structures.GeneralConfig.sim_tool` value."""
    get_sim_tool_implementation(state.general.sim_tool).simulation_stage(state)
