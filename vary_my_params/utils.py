import cProfile
import functools
import io
import logging
import pstats
import sys
import time
from pstats import SortKey
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import Config


def get_answer(config: "Config", question: str, exit_if_no: bool = False) -> bool:
    """Ask a yes/no question on the command line and return True if the answer is yes and False if the answer is no"""
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
