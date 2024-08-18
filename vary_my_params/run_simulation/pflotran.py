import os
import subprocess

from ..config import Config


def run_simulation(config: Config):
    original_dir = os.getcwd()

    for index in range(config.general.number_datapoints):
        os.chdir(config.general.output_directory / f"datapoint-{index}")
        subprocess.run(["mpirun", "-n", "1", "pflotran"], check=True, close_fds=True)
        # always go back to the original_dir as we use relative paths
        os.chdir(original_dir)
