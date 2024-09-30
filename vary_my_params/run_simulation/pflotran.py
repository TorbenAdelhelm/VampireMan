import logging
import os
import subprocess

from ..config import Config
from ..utils import get_answer


def run_simulation(config: Config):
    original_dir = os.getcwd()

    for index in range(config.general.number_datapoints):
        datapoint_path = config.general.output_directory / f"datapoint-{index}"
        os.chdir(datapoint_path)
        if os.path.exists("pflotran.out") and os.path.exists("pflotran.h5"):
            logging.warn(f"pflotran.out and pflotran.h5 files present in {datapoint_path}")
            if not get_answer(config, "Looks like the simulation already ran, run simulation again?"):
                os.chdir(original_dir)
                continue

        command: list[str] = []
        if config.general.mpirun:
            command += ["mpirun", "-n", str(config.general.mpirun_procs)]
        command += ["pflotran"]
        if config.general.mute_simulation_output:
            command += ["-screen_output", "off"]
        subprocess.run(command, check=True, close_fds=True)

        # always go back to the original_dir as we use relative paths
        os.chdir(original_dir)
