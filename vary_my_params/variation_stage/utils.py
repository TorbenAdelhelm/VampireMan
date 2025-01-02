from ..data_structures import State
from ..utils import get_answer, profile_function, write_data_to_verified_json_file
from .vary import vary_params


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
