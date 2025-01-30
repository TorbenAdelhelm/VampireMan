"""
The loading stage takes care of initializing the `vampireman.data_structures.State` object which is used throughout the
pipeline run.

First, a `vampireman.data_structures.State` object is created with all its default values in place.
Then, if the user provided a settings file via the `--settings-file` command line parameter, the given yaml file is read
and another `vampireman.data_structures.State` object with the values from the yaml is instantiated.
Afterwards, the first object is overridden with the second one to keep the default settings without the user having to
explicitly specify everything.
"""

import argparse
import logging

from ..data_structures import State


def loading_stage(arguments: argparse.Namespace) -> State:
    """
    Run the stage.
    """

    run_state = State()
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
        logging.info("Running interactively")
    else:
        logging.info("Running non-interactively")

    logging.debug("Resulting state of load_state: %s", run_state)

    return run_state
