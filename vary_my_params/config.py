import argparse
import logging
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class Config:
    # Need to use field here, as otherwise it would be the same dict across several objects
    general: dict[str, Any] = field(
        default_factory=lambda: {
            "interactive": True,
            "output_directory": "./out_dir",
            # This forces every run to be reproducible by default!
            "random_seed": 0,
            "workflow": "pflotran",
        }
    )
    steps: list[str] = field(default_factory=lambda: ["global"])
    parameters: dict[str, Any] = field(default_factory=lambda: {})
    data: dict[str, Any] = field(default_factory=lambda: {})

    def override_with(self, other_config: "Config"):
        self.general |= other_config.general
        self.parameters |= other_config.parameters
        self.steps = other_config.steps or self.steps

    @staticmethod
    def from_yaml(config_file_path: str) -> "Config":
        logging.debug("Trying to load config from %s", config_file_path)
        try:
            with open(config_file_path, encoding="utf-8") as config_file:
                yaml_values = yaml.safe_load(config_file)
        except OSError as err:
            logging.error("Could not find config file '%s', %s", config_file_path, err)
            raise err
        logging.debug("Loaded config from %s", config_file_path)
        logging.debug("Yaml: %s", yaml_values)

        user_config = Config()

        user_config.general = yaml_values.get("general", {})
        user_config.parameters = yaml_values.get("parameters", {})
        user_config.steps = yaml_values.get("steps", [])

        return user_config


def load_config(arguments: argparse.Namespace) -> Config:
    # XXX: No idea if we can dynamically load other configs...
    # ... also unsure if this is even a good idea
    # import importlib
    # try:
    #     lib = importlib.import_module(args.workflow, "default_config")
    #     importlib.invalidate_caches()
    #     logging.info(lib.__name__)
    #     logging.info(lib.pflotran.get_defaults())
    #
    # except Exception as err:
    #     logging.error(err)

    # Get workflow specific defaults
    match arguments.workflow:
        case "pflotran":
            from .default_config import pflotran as config_module
        case _:
            logging.error("%s workflow is not yet implemented", arguments.workflow)
            raise NotImplementedError("Workflow not implemented")

    workflow_specific_default_config = config_module.get_defaults()

    run_config = Config()
    run_config.override_with(workflow_specific_default_config)

    # Load config from file if provided
    config_file = arguments.config_file
    if config_file is not None:
        user_config = Config.from_yaml(config_file)
        run_config.override_with(user_config)

    # Also consider arguments from command line
    run_config.general["interactive"] = not arguments.non_interactive
    if arguments.non_interactive:
        logging.debug("Running non-interactively")

    logging.debug("Config: %s", run_config)

    return run_config
