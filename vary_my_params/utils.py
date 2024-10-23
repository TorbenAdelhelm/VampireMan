import cProfile
import functools
import hashlib
import io
import logging
import os
import pstats
import sys
import time
from pstats import SortKey
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config


def get_answer(config: "Config", question: str, exit_if_no: bool = False) -> bool:
    """Ask a yes/no question on the command line and return True if the answer is yes and False if the answer is
    no. When CTRL+C is detected, the function will terminate the whole program returning an exit code of 0.
    """

    if not config.general.interactive:
        return True
    try:
        match input(f"{question} Y/n "):
            case "n" | "N" | "no" | "q":
                if exit_if_no:
                    logging.info("Exiting as instructed")
                    sys.exit(0)
                return False
            case _:
                return True
    except KeyboardInterrupt:
        logging.info("Exiting as instructed")
        sys.exit(0)


def get_workflow_module(workflow: str) -> ModuleType:
    # Get workflow specific defaults
    match workflow:
        case "pflotran":
            from . import pflotran

            return pflotran
        case _:
            logging.error("%s workflow is not yet implemented", workflow)
            raise NotImplementedError("Workflow not implemented")


def profile_function(function):
    @functools.wraps(function)
    def wrapper(*args):
        config: Config = args[0]

        if config.general.profiling:
            profile = cProfile.Profile()

            start_time = time.perf_counter()

            profile.enable()

            result = function(*args)

            profile.disable()

            end_time = time.perf_counter()
            run_time = end_time - start_time
            logging.info("Function %s.%s took %s", function.__module__, function.__name__, run_time)

            s = io.StringIO()
            ps = pstats.Stats(profile, stream=s).sort_stats(SortKey.CUMULATIVE)
            ps.print_stats()

            with open(f"profiling_{function.__module__}.{function.__name__}.txt", "w") as file:
                file.write(s.getvalue())
        else:
            result = function(*args)

        return result

    return wrapper


def create_dataset_and_datapoint_dirs(config: "Config"):
    for index in range(config.general.number_datapoints):
        datapoint_dir = config.general.output_directory / f"datapoint-{index}"
        try:
            os.makedirs(datapoint_dir, exist_ok=True)
        except OSError as error:
            logging.critical("Directory at %s could not be created, cannot proceed", datapoint_dir)
            raise error


def write_config_to_output_dir(config: "Config"):
    config_target_path = config.general.output_directory / "config.json"

    # Check if there already is a config file
    if os.path.isfile(config_target_path):
        with open(config_target_path) as config_file:
            config_file_content = config_file.read()

        # Calculate the hash from current config and the existing config.json file
        hash_in_memory = hashlib.sha256(config.model_dump_json(indent=2).encode()).hexdigest()
        hash_config_file = hashlib.sha256(config_file_content.encode()).hexdigest()

        # If there is, compare the contents to let the user abort
        if hash_in_memory != hash_config_file:
            logging.warning("Config file in output_directory has different contents!")
            if not get_answer(
                config, f"Different config file already in {config.general.output_directory}, overwrite?"
            ):
                config.pure = False
                return

    with open(config_target_path, "w") as config_file:
        config_file.write(config.model_dump_json(indent=2))
