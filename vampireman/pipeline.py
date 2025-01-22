import logging
from argparse import Namespace

from .loading_stage import loading_stage
from .preparation_stage import preparation_stage
from .render_stage import render_stage
from .simulation_stage import simulation_stage
from .utils import get_answer
from .validation_stage import validation_stage
from .variation_stage import variation_stage
from .visualization_stage import visualization_stage


def run(args: Namespace):
    state = loading_stage(args)
    state = preparation_stage(state)
    state = validation_stage(state)

    # Where do we check this?
    logging.debug("Will run all stages")

    print("This is the state that is going to be used:")
    print(state)

    get_answer(state, "Do you want to run the variation stage?", True)
    state = variation_stage(state)

    get_answer(state, "Do you want to run the render stage?", True)
    render_stage(state)

    get_answer(state, "Do you want to run the simulation stage?", True)
    simulation_stage(state)

    get_answer(state, "Do you want to run the visualization stage?", True)
    visualization_stage(state)
