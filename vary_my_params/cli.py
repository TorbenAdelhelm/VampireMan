"""This is the interface allowing a user to interact with the tool via a command line. It exposes common functions in a
structured way."""

import argparse
import logging
import pathlib

import vary_my_params.prepare_simulation.pflotran.pflotran_in_renderer as pflotran


def main():
    logging.info("staring up")
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", type=pathlib.Path, default="./config.yaml", help="number of datapoints to generate")
    parser.add_argument("--datapoints", type=int, default=1, help="number of datapoints to generate")
    parser.add_argument("--name", type=str, default="default", help="name of the simulation")

    args = parser.parse_args()
    print(args)

    pflotran.render()
