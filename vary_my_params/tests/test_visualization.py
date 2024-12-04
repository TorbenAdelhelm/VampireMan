import os

from vary_my_params.config import State
from vary_my_params.pipeline import preparation_stage, render_stage, simulation_stage, vary_stage, visualization_stage
from vary_my_params.utils import create_dataset_and_datapoint_dirs


def test_vis_files_not_empty(tmp_path):
    state = State()
    state.general.interactive = False
    state.general.mpirun = False
    state.general.output_directory = tmp_path / "render_test"
    state.general.number_cells = [32, 64, 2]

    create_dataset_and_datapoint_dirs(state)
    state = preparation_stage(state)
    state = vary_stage(state)
    render_stage(state)
    simulation_stage(state)
    visualization_stage(state)

    datapoint_path = tmp_path / "render_test" / "datapoint-0"
    assert os.path.exists(datapoint_path)

    for file in [
        "permeability_field.png",
        "Pflotran_isolines.jpg",
        "Pflotran_properties_2d.jpg",
    ]:
        # Check if files are not empty
        # TODO: Better test
        assert os.path.getsize(datapoint_path / file) > 0
