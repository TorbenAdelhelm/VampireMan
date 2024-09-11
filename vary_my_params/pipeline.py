import cProfile
import io
import logging
import pstats
from argparse import Namespace
from collections.abc import Callable
from pstats import SortKey

from .config import Config, Workflow, load_config
from .load_config.pflotran import ensure_config_is_valid
from .prepare_simulation.pflotran.pflotran_in_renderer import render
from .run_simulation.pflotran import run_simulation as run_pflotran
from .utils import get_answer
from .vary_params import pflotran
from .visualize.pflotran import plot_sim


def run_vary_params(config: Config) -> Config:
    get_answer(config, "Do you want to run the stage parameter variation?", True)

    match config.general.workflow:
        case Workflow.PFLOTRAN:
            data = pflotran.vary_params(config)
            print("Following datapoints will be used")
            for datapoint in data.datapoints:
                print(datapoint)
            return data
        case _:
            logging.error("%s varying is not yet implemented", config.general.workflow)
            raise NotImplementedError()


def run_render(config: Config):
    get_answer(config, "Do you want to run the stage prepare_simulation?", True)
    render(config)


def run_simulation(config: Config):
    get_answer(config, "Do you want to run the stage run_simulation?", True)
    run_pflotran(config)


def run_visualization(config: Config):
    get_answer(config, "Do you want to run the stage run_visualization?", True)
    plot_sim(config)


def profile_stage(config: Config, stage: Callable[[Config], None | Config]):
    result = None

    if config.general.profiling:
        profile = cProfile.Profile()
        profile.enable()

        result = stage(config)

        profile.disable()
        s = io.StringIO()
        ps = pstats.Stats(profile, stream=s).sort_stats(SortKey.CUMULATIVE)
        ps.print_stats()

        with open(f"profiling_{stage.__name__}.txt", "w") as file:
            file.write(s.getvalue())
    else:
        result = stage(config)

    return result


def run(args: Namespace):
    config = load_config(args)
    profile_stage(config, ensure_config_is_valid)

    print(config)
    logging.debug("Will run all stages")

    config = profile_stage(config, run_vary_params)
    assert config is not None

    profile_stage(config, run_render)
    # XXX: visualize in between the steps
    profile_stage(config, run_simulation)
    profile_stage(config, run_visualization)
