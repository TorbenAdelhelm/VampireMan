from argparse import Namespace
from pathlib import Path

from vampireman.data_structures import State
from vampireman.loading_stage import loading_stage
from vampireman.render_stage import render_stage
from vampireman.pipeline import preparation_stage, variation_stage
from vampireman.utils import create_dataset_and_datapoint_dirs, write_data_to_verified_json_file
from vampireman.validation_stage.utils import validation_stage


def test_all_settings(tmp_path):
    pathlist = Path("./settings/").glob("*.yaml")
    for setting in pathlist:
        try:
            state = State.from_yaml(setting)
            state = loading_stage(
                Namespace(settings_file=setting, sim_tool="pflotran", non_interactive=True, log_level="INFO")
            )
            state.general.output_directory = tmp_path / f"render_test/{setting}"
            if state.general.number_cells[0] * state.general.number_cells[1] * state.general.number_cells[2] > 50000:
                # Skipping as large settings take ages
                continue
            state = preparation_stage(state)
            state = validation_stage(state)
            create_dataset_and_datapoint_dirs(state)
            write_data_to_verified_json_file(state, state.general.output_directory / "state.json", state)
            state = variation_stage(state)
            render_stage(state)
        except Exception as e:
            print(f"Error in {setting}")
            raise e
