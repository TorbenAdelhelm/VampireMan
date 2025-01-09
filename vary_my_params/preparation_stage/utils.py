from ..data_structures import State
from ..utils import create_dataset_and_datapoint_dirs, profile_function, read_in_files
# TODO why from the variation_stage?
from ..variation_stage.vary import (
    calculate_frequencies,
    calculate_hp_coordinates,
    generate_heatpumps,
    handle_time_based_params,
)


@profile_function
def preparation_stage(state: State) -> State:
    create_dataset_and_datapoint_dirs(state)
    state = read_in_files(state)
    state = calculate_frequencies(state)
    state = generate_heatpumps(state)
    state = calculate_hp_coordinates(state)
    state = handle_time_based_params(state)
    return state
