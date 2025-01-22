from ..data_structures import State
from ..utils import profile_function, write_data_to_verified_json_file
from .vary import vary_params


@profile_function
def variation_stage(state: State) -> State:
    state = vary_params(state)
    print("Following datapoints will be used")
    for datapoint in state.datapoints:
        print(datapoint)
        write_data_to_verified_json_file(
            state, state.general.output_directory / f"datapoint-{datapoint.index}" / "datapoint.json", datapoint
        )
    return state
