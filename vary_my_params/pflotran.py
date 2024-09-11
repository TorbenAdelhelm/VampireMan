from .config import Config
from .load_config import pflotran as pflotran_config
from .prepare_simulation import pflotran as pflotran_render
from .run_simulation import pflotran as pflotran_run
from .vary_params import pflotran as pflotran_vary
from .visualize import pflotran as pflotran_visualize


def get_defaults() -> Config:
    return pflotran_config.get_defaults()


def ensure_config_is_valid(config: Config):
    return pflotran_config.ensure_config_is_valid(config)


def render(config: Config):
    return pflotran_render.render(config)


def vary_params(config: Config):
    return pflotran_vary.vary_params(config)


def run_simulation(config: Config):
    return pflotran_run.run_simulation(config)


def plot_simulation(config: Config):
    return pflotran_visualize.plot_simulation(config)
