import argparse
import logging

from ..config import State


def loading_stage(arguments: argparse.Namespace) -> State:
    run_state = State()  # pyright: ignore
    logging.debug("Default state is %s", run_state)

    # Load settings from file if provided
    settings_file = arguments.settings_file
    if settings_file is not None:
        user_settings = State.from_yaml(settings_file)
        run_state.override_with(user_settings)

    # Also consider arguments from command line
    if arguments.non_interactive:
        run_state.general.interactive = False

    if run_state.general.interactive:
        logging.info("Running non-interactively")

    logging.debug("Resulting state of load_state: %s", run_state)

    return run_state
