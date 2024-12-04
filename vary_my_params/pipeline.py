import logging
from argparse import Namespace

from .config import State, validation_stage, loading_stage
from .utils import (
    create_dataset_and_datapoint_dirs,
    get_answer,
    get_workflow_module,
    profile_function,
    read_in_files,
    write_data_to_verified_json_file,
)
from .vary_params.vary import (
    calculate_frequencies,
    calculate_hp_coordinates,
    generate_heatpumps,
    handle_time_based_params,
    vary_params,
)


@profile_function
def preparation_stage(state: State) -> State:
    state = read_in_files(state)
    state = calculate_frequencies(state)
    state = generate_heatpumps(state)
    state = calculate_hp_coordinates(state)
    state = handle_time_based_params(state)
    return state


@profile_function
def variation_stage(state: State) -> State:
    get_answer(state, "Do you want to run the variation stage?", True)
    state = vary_params(state)
    print("Following datapoints will be used")
    for datapoint in state.datapoints:
        print(datapoint)
        write_data_to_verified_json_file(
            state, state.general.output_directory / f"datapoint-{datapoint.index}" / "datapoint.json", datapoint
        )
    return state


@profile_function
def render_stage(state: State):
    get_answer(state, "Do you want to run the render stage?", True)
    get_workflow_module(state.general.workflow).render_stage(state)


@profile_function
def simulation_stage(state: State):
    get_answer(state, "Do you want to run the simulation stage?", True)
    get_workflow_module(state.general.workflow).simulation_stage(state)


@profile_function
def visualization_stage(state: State):
    get_answer(state, "Do you want to run the visualization stage?", True)
    get_workflow_module(state.general.workflow).visualization_stage(state)


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
