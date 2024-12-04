import os

from vary_my_params.config import State
from vary_my_params.pipeline import preparation_stage, render_stage, variation_stage
from vary_my_params.utils import create_dataset_and_datapoint_dirs


def test_render_borders_and_mesh(tmp_path):
    state = State()
    state.general.interactive = False
    state.general.output_directory = tmp_path / "render_test"
    state.general.number_cells = [32, 64, 2]

    create_dataset_and_datapoint_dirs(state)
    render_stage(state)

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
    state = State()
    state.general.interactive = False
    state.general.output_directory = tmp_path / "render_test"
    state.general.number_datapoints = 2

    create_dataset_and_datapoint_dirs(state)
    state = preparation_stage(state)
    state = variation_stage(state)
    render_stage(state)

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
