import logging
from argparse import Namespace

from .config import State, ensure_state_is_valid, load_state
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
def prepare_parameters(state: State) -> State:
    state = read_in_files(state)
    state = calculate_frequencies(state)
    state = generate_heatpumps(state)
    state = calculate_hp_coordinates(state)
    state = handle_time_based_params(state)
    return state


@profile_function
def run_vary_params(state: State) -> State:
    get_answer(state, "Do you want to run the stage parameter variation?", True)
    state = vary_params(state)
    print("Following datapoints will be used")
    for datapoint in state.datapoints:
        print(datapoint)
        write_data_to_verified_json_file(
            state, state.general.output_directory / f"datapoint-{datapoint.index}" / "datapoint.json", datapoint
        )
    return state


@profile_function
def run_render(state: State):
    get_answer(state, "Do you want to run the stage prepare_simulation?", True)
    get_workflow_module(state.general.workflow).render(state)


@profile_function
def run_simulation(state: State):
    get_answer(state, "Do you want to run the stage run_simulation?", True)
    get_workflow_module(state.general.workflow).run_simulation(state)


@profile_function
def run_visualization(state: State):
    get_answer(state, "Do you want to run the stage run_visualization?", True)
    get_workflow_module(state.general.workflow).plot_simulation(state)


def run(args: Namespace):
    state = load_state(args)
    state = prepare_parameters(state)
    state = ensure_state_is_valid(state)

    create_dataset_and_datapoint_dirs(state)
    write_data_to_verified_json_file(state, state.general.output_directory / "state.json", state)

    # Where do we check this?
    logging.debug("Will run all stages")

    print("This is the state that is going to be used:")
    print(state)

    state = run_vary_params(state)

    run_render(state)
    run_simulation(state)
    run_visualization(state)
