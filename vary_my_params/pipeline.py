import logging
from argparse import Namespace

from .data_structures import State
from .loading_stage import loading_stage
from .preparation_stage import preparation_stage
from .utils import (
    create_dataset_and_datapoint_dirs,
    get_answer,
    get_numerical_solver_implementation,
    profile_function,
    write_data_to_verified_json_file,
)
from .validation_stage import validation_stage
from .variation_stage import variation_stage


@profile_function
def render_stage(state: State):
    get_answer(state, "Do you want to run the render stage?", True)
    get_numerical_solver_implementation(state.general.numerical_solver).render_stage(state)


@profile_function
def simulation_stage(state: State):
    get_answer(state, "Do you want to run the simulation stage?", True)
    get_numerical_solver_implementation(state.general.numerical_solver).simulation_stage(state)


@profile_function
def visualization_stage(state: State):
    get_answer(state, "Do you want to run the visualization stage?", True)
    get_numerical_solver_implementation(state.general.numerical_solver).visualization_stage(state)


def run(args: Namespace):
    state = loading_stage(args)
    state = preparation_stage(state)
    state = validation_stage(state)

    create_dataset_and_datapoint_dirs(state)
    write_data_to_verified_json_file(state, state.general.output_directory / "state.json", state)

    # Where do we check this?
    logging.debug("Will run all stages")

    print("This is the state that is going to be used:")
    print(state)

    state = variation_stage(state)

    render_stage(state)
    simulation_stage(state)
    visualization_stage(state)
