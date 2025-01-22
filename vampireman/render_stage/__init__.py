"""The render stage..."""

from ..data_structures import State
from ..utils import get_sim_tool_implementation, profile_function


@profile_function
def render_stage(state: State):
    """This function runs the simulation tool render stage based on the
    `vampireman.data_structures.GeneralConfig.sim_tool` value."""
    get_sim_tool_implementation(state.general.sim_tool).render_stage(state)
