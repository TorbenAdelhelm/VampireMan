import cProfile
import functools
import hashlib
import io
import json
import logging
import os
import pstats
import sys
import time
from pathlib import Path
from pstats import SortKey
from types import ModuleType
from typing import TYPE_CHECKING

import numpy as np
from h5py import File
from pydantic import BaseModel

from .data_structures import Datapoint

if TYPE_CHECKING:
    from .data_structures import State


def get_answer(state: "State", question: str, exit_if_no: bool = False) -> bool:
    """Ask a yes/no question on the command line and return True if the answer is yes and False if the answer is
    no. When CTRL+C is detected, the function will terminate the whole program returning an exit code of 0.
    """

    if not state.general.interactive:
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


def get_numerical_solver_implementation(numerical_solver: str) -> ModuleType:
    # Get solver specific defaults
    match numerical_solver:
        case "pflotran":
            from . import pflotran

            return pflotran
        case _:
            logging.error("%s numerical solver is not yet implemented", numerical_solver)
            raise NotImplementedError("Numerical solver not implemented")


def profile_function(function):
    @functools.wraps(function)
    def wrapper(*args):
        state: State = args[0]

        if state.general.profiling:
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

            with open(
                f"profiling/{state.general.output_directory.name}_{function.__module__}.{function.__name__}.txt", "w"
            ) as file:
                file.write(s.getvalue())
        else:
            result = function(*args)

        return result

    return wrapper


def create_dataset_and_datapoint_dirs(state: "State"):
    for index in range(state.general.number_datapoints):
        datapoint_dir = state.general.output_directory / f"datapoint-{index}"
        try:
            os.makedirs(datapoint_dir, exist_ok=True)
        except OSError as error:
            logging.critical("Directory at %s could not be created, cannot proceed", datapoint_dir)
            raise error


def write_data_to_verified_json_file(state: "State", target_path: Path, data: BaseModel):
    """Write a `pydantic.main.BaseModel` to a file and ask the user how to proceed, if there is already a file present
    with different contents than the data that is represented in `data`. The data will be written in json format."""

    need_to_write_file = True

    # Write hash of permeability content into permeability field
    # This avoids putting hundreds of MB of numbers into the file when handling large perm fields
    if isinstance(data, Datapoint):
        perm = data.data.get("permeability")
        assert perm is not None  # Should never happen, make the linter happy
        perm_value = perm.value
        data.data["permeability"].value = hashlib.sha256(perm.model_dump_json(indent=2).encode()).hexdigest()

    # Check if there already is a target file
    if os.path.isfile(target_path):
        with open(target_path, encoding="utf8") as target_file:
            target_file_content = target_file.read()

        # Calculate the hash from the data object and the existing target file
        hash_in_memory = hashlib.sha256(data.model_dump_json(indent=2).encode()).hexdigest()
        hash_target_file = hashlib.sha256(target_file_content.encode()).hexdigest()

        # If there is, compare the contents to let the user abort
        if hash_in_memory != hash_target_file:
            logging.warning("Target file '%s' has different contents than data structure!", target_path)
            if not get_answer(state, f"Different target file already in {target_path}, overwrite?"):
                need_to_write_file = False
        else:
            logging.debug("File '%s' doesn't need to be written", target_path)

    if need_to_write_file:
        with open(target_path, "w", encoding="utf8") as target_file:
            target_file.write(data.model_dump_json(indent=2))

    if isinstance(data, Datapoint):
        # Restore the previous actual value
        perm.value = perm_value


def read_in_files(state: "State"):
    for parameter_name, parameter in (state.hydrogeological_parameters | state.heatpump_parameters).items():
        if not isinstance(parameter.value, Path):
            continue

        try:
            if parameter.value.suffix in [".H5", ".h5"]:
                with File(parameter.value) as h5file:
                    if parameter_name.title() not in h5file:
                        raise KeyError("Could not find '%s' in the h5 file", parameter_name.title())
                    parameter.value = np.array(h5file[parameter_name.title()])

            elif parameter.value.suffix in [".json"]:
                with open(parameter.value) as value_file:
                    parameter.value = json.load(value_file)

            elif parameter.value.suffix in [".txt", ""]:
                with open(parameter.value) as value_file:
                    parameter.value = value_file.read()

            else:
                msg = f"Don't know what to do with the extension '{parameter.value.suffix}'"
                logging.error(msg)
                raise ValueError(msg)

        except (FileNotFoundError, PermissionError) as error:
            raise OSError(f"Could not open value file '{parameter_name}' for parameter '{parameter.value}'") from error

    return state
