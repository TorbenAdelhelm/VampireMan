"""This is the interface allowing a user to interact with the tool via a command line. It exposes common functions in a
structured way."""

import argparse
import logging
import pathlib

from . import pipeline


def main():
    logging.info("Staring up")
    parser = argparse.ArgumentParser(
        prog="python3 -m vampireman",
        description="This program implements a pipeline that varies parameters for a simulation in a structured way",
    )

    parser.add_argument("--settings-file", type=pathlib.Path, help="number of datapoints to generate")
    parser.add_argument("--sim-tool", type=str, default="pflotran", help="name of the simulation tool implementation")
    parser.add_argument("--non-interactive", action="store_true", default=None, help="don't ask for user confirmation")
    parser.add_argument("--log-level", type=str, default="INFO", help="enable debug logging")

    args = parser.parse_args()

    if args.log_level:
        logging.getLogger().setLevel(args.log_level)
        logging.debug("Set logger to level %s", args.log_level)

    logging.debug("Arguments are: %s", args)

    pipeline.run(args)
