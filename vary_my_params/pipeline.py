import cProfile
import io
import logging
import pstats
from argparse import Namespace
from collections.abc import Callable
from pstats import SortKey

from .config import Config, load_config
from .utils import get_answer, get_workflow_module


def run_vary_params(config: Config) -> Config:
    get_answer(config, "Do you want to run the stage parameter variation?", True)
    config = get_workflow_module(config.general.workflow).vary_params(config)
    print("Following datapoints will be used")
    for datapoint in config.datapoints:
        print(datapoint)
    return config


def run_render(config: Config):
    get_answer(config, "Do you want to run the stage prepare_simulation?", True)
    get_workflow_module(config.general.workflow).render(config)


def run_simulation(config: Config):
    get_answer(config, "Do you want to run the stage run_simulation?", True)
    get_workflow_module(config.general.workflow).run_simulation(config)


def run_visualization(config: Config):
    get_answer(config, "Do you want to run the stage run_visualization?", True)
    get_workflow_module(config.general.workflow).plot_simulation(config)


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
    workflow_module = get_workflow_module(args.workflow)

    config = load_config(args, workflow_module)

    profile_stage(config, workflow_module.ensure_config_is_valid)

    print(config)
    logging.debug("Will run all stages")

    config = profile_stage(config, run_vary_params)
    assert config is not None

    profile_stage(config, run_render)
    # XXX: visualize in between the steps
    profile_stage(config, run_simulation)
    profile_stage(config, run_visualization)
