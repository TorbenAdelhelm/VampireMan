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
from .vary_params import pflotran
from .visualize.pflotran import plot_sim


def wait_for_confirmation(config: Config, next_stage: str = ""):
    if not config.general.interactive:
        return
    try:
        match input(f"Do you want to continue? {f"Next stage: {next_stage} " if next_stage else ""}Y/n "):
            case "n" | "N" | "no" | "q":
                logging.info("Exiting as instructed")
                exit(0)
            case _:
                pass
    except KeyboardInterrupt:
        logging.info("Exiting as instructed")
        exit(0)


def run_vary_params(config: Config) -> Config:
    wait_for_confirmation(config, "Running stage parameter variation")

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
    wait_for_confirmation(config, "Running stage prepare_simulation")
    render(config)


def run_simulation(config: Config):
    wait_for_confirmation(config, "Running stage run_simulation")
    run_pflotran(config)


def run_visualization(config: Config):
    wait_for_confirmation(config, "Running stage run_visualization")
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
    profile_stage(config, run_simulation)
    profile_stage(config, run_visualization)
