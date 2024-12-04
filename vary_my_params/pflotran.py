from .config import State
from .prepare_simulation import pflotran as pflotran_render
from .run_simulation import pflotran as pflotran_run
from .visualize import pflotran as pflotran_visualize


def render_stage(config: State):
    return pflotran_render.render_stage(config)


def simulation_stage(config: State):
    return pflotran_run.simulation_stage(config)


def visualization_stage(config: State):
    return pflotran_visualize.visualization_stage(config)
