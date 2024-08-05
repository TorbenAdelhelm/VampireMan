import os
import subprocess

from ..config import Config


def run_simulation(config: Config):
    original_dir = os.getcwd()

    for index in range(config.general.number_datapoints):
        # always go back to the original_dir as we use relative paths
        os.chdir(original_dir)
        os.chdir(config.general.output_directory / f"datapoint-{index}")
        subprocess.run(["pflotran"])
