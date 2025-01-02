import pytest
from vary_my_params.data_structures import Parameter, State, Vary, HeatPump
from vary_my_params.loading_stage.utils import loading_stage
from vary_my_params.pipeline import preparation_stage, render_stage, variation_stage
from vary_my_params.utils import create_dataset_and_datapoint_dirs, write_data_to_verified_json_file
from vary_my_params.validation_stage.utils import validation_stage


def test_validation_stage_heatpump_in_hgp():
    state = State()
    state.general.interactive = False

    state.hydrogeological_parameters["heatpump"] = Parameter(
        name="hp1",
        vary=Vary.SPACE,
        value=HeatPump(location=[16, 32, 1], injection_temp=13.6, injection_rate=0.00024),
    )

    state = preparation_stage(state)
    with pytest.raises(ValueError):
        state = validation_stage(state)


def test_validation_stage_empty_hgp():
    state = State()
    state.general.interactive = False

    state.hydrogeological_parameters = {}

    state = preparation_stage(state)
    with pytest.raises(ValueError):
        state = validation_stage(state)
