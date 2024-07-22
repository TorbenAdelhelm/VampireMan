import logging
from argparse import Namespace

from .config import Config, load_config
from .prepare_simulation.pflotran.pflotran_in_renderer import render
from .vary_params import pflotran


def run_vary_params(config: Config) -> Config:
    logging.debug(config.general)

    match config.general.get("workflow"):
        case "pflotran":
            return pflotran.vary_params(config)
        case _:
            logging.error("%s varying is not yet implemented", config.general.get("workflow"))
            raise NotImplementedError()


def run_all(config: Config):
    logging.debug("Will run all stages")
    config = run_vary_params(config)
    render(config)


def run(args: Namespace):
    config = load_config(args)

    match args.stages.split(","):
        case ["all"]:
            run_all(config)
        case _:
            logging.error("Stage not found")
