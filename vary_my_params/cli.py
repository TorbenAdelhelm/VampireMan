"""This is the interface allowing a user to interact with the tool via a command line. It exposes common functions in a
structured way."""

import argparse
import logging
import pathlib

from . import pipeline


def main():
    logging.info("Staring up")
    parser = argparse.ArgumentParser(
        prog="Vary My Params",
        description="This program implements a pipeline that varies parameters for a simulation in a structured way",
    )

    parser.add_argument("--config-file", type=pathlib.Path, help="number of datapoints to generate")
    parser.add_argument("--workflow", type=str, default="pflotran", help="name of the simulation workflow")
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        default=None,
        help="don't ask for user confirmation to move to next stage",
    )
    parser.add_argument("--log-level", type=str, default="INFO", help="enable debug logging")

    args = parser.parse_args()

    if args.log_level:
        logging.getLogger().setLevel(args.log_level)

    pipeline.run(args)
