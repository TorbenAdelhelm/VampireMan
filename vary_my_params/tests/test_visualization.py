import os

from vary_my_params.config import Config
from vary_my_params.pipeline import prepare_parameters, run_render, run_simulation, run_vary_params, run_visualization
from vary_my_params.utils import create_dataset_and_datapoint_dirs


def test_vis_files_not_empty(tmp_path):
    config = Config()
    config.general.interactive = False
    config.general.mpirun = False
    config.general.output_directory = tmp_path / "render_test"
    config.general.number_cells = [32, 64, 2]

    create_dataset_and_datapoint_dirs(config)
    config = prepare_parameters(config)
    config = run_vary_params(config)
    run_render(config)
    run_simulation(config)
    run_visualization(config)

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
