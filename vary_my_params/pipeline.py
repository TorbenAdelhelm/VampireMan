import logging
from argparse import Namespace

from .config import Config, load_config


def run_vary_params(config: Config):
    logging.debug(config.general)


def run_all(config: Config):
    logging.debug("Will run all stages")
    run_vary_params(config)


def run(args: Namespace):
    config = load_config(args)

    match args.stages.split(","):
        case ["all"]:
            run_all(config)
        case _:
            logging.error("Stage not found")
