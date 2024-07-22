"""This is the interface allowing a user to interact with the tool via a command line. It exposes common functions in a
structured way."""

import argparse
import logging
import pathlib

from .pipeline import run


def main():
    logging.info("staring up")
    parser = argparse.ArgumentParser()

    parser.add_argument("--config-file", type=pathlib.Path, help="number of datapoints to generate")
    parser.add_argument("--datapoints", type=int, default=1, help="number of datapoints to generate")
    parser.add_argument("--name", type=str, default="default", help="name of the simulation")
    parser.add_argument("--workflow", type=str, default="pflotran", help="name of the simulation workflow")
    parser.add_argument("--stages", type=str, default="all", help="name of the pipeline stages to run")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run(args)
