import os

from vary_my_params.config import Config
from vary_my_params.pipeline import prepare_parameters, run_render, run_vary_params
from vary_my_params.utils import create_dataset_and_datapoint_dirs


def test_render_borders_and_mesh(tmp_path):
    config = Config()
    config.general.interactive = False
    config.general.output_directory = tmp_path / "render_test"
    config.general.number_cells = [32, 64, 2]

    create_dataset_and_datapoint_dirs(config)
    run_render(config)

    for file in [
        "east.ex",
        "west.ex",
    ]:
        file_path = tmp_path / "render_test" / file
        assert os.path.exists(file_path)

        with open(file_path) as f:
            lines = f.readlines()
            assert lines[0] == "CONNECTIONS 128\n"
            assert len(lines) == 64 * 2 + 1

    for file in [
        "north.ex",
        "south.ex",
    ]:
        file_path = tmp_path / "render_test" / file
        assert os.path.exists(file_path)

        with open(file_path) as f:
            lines = f.readlines()
            assert lines[0] == "CONNECTIONS 64\n"
            assert len(lines) == 32 * 2 + 1

    mesh_path = tmp_path / "render_test" / "mesh.uge"
    assert os.path.exists(mesh_path)
    with open(mesh_path) as f:
        lines = f.readlines()
        assert lines[0] == "CELLS 4096\n"
        # This is two text lines plus 64 * 32 * 2 cells plus 10048 connections
        assert len(lines) == 2 + 64 * 32 * 2 + 10048


def test_render_files_not_empty(tmp_path):
    config = Config()
    config.general.interactive = False
    config.general.output_directory = tmp_path / "render_test"
    config.general.number_datapoints = 2

    create_dataset_and_datapoint_dirs(config)
    config = prepare_parameters(config)
    config = run_vary_params(config)
    run_render(config)

    for dir in [
        "datapoint-0",
        "datapoint-1",
    ]:
        datapoint_path = tmp_path / "render_test" / dir
        assert os.path.exists(datapoint_path)

        for file in [
            "permeability_field.h5",
            "pflotran.in",
        ]:
            # Check if files are not empty
            # TODO: Better test
            assert os.path.getsize(datapoint_path / file) > 0
