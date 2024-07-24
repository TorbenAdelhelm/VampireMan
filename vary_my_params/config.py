import argparse
import enum
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

yaml = YAML(typ="safe")


class DataType(enum.StrEnum):
    SCALAR = "scalar"
    ARRAY = "array"


class Vary(enum.StrEnum):
    # XXX: Is this fixed, vary_within_datapoint etc?
    NONE = "none"


class InputSource(enum.StrEnum):
    MANUAL = "manual"


class Workflow(enum.StrEnum):
    PFLOTRAN = "pflotran"


@dataclass
class Parameter:
    name: str
    data_type: DataType
    value: Any
    vary: Vary = Vary.NONE
    input_source: InputSource = InputSource.MANUAL

    @staticmethod
    def from_dict(name: str, conf: dict[str, Any]) -> "Parameter":
        if conf == {}:
            raise ValueError("Parameter config is empty")

        if not isinstance(name, str):
            raise ValueError("`name` is not of type str")

        data_type = conf.pop("data_type", None)
        if data_type is None:
            raise ValueError("`data_type` missing from parameter")
        if isinstance(data_type, str):
            data_type = DataType(data_type)
        if not isinstance(data_type, DataType):
            raise ValueError("`data_type` is not of type DataType")

        # Value could probably be None, so we can't use the same logic here
        if "value" not in conf:
            raise ValueError("`value` missing from parameter")
        value = conf.pop("value")

        result = Parameter(name, data_type, value)

        vary = conf.pop("vary", None)
        if vary is not None:
            if isinstance(vary, str):
                vary = Vary(vary)
            if not isinstance(vary, Vary):
                raise ValueError("`vary` is not of type Vary")
            result.vary = vary

        input_source = conf.pop("input_source", None)
        if input_source is not None:
            if isinstance(input_source, str):
                input_source = InputSource(input_source)
            if not isinstance(input_source, InputSource):
                raise ValueError("`input_source` is not of type InputSource")
            result.input_source = input_source

        return result

    def __str__(self) -> str:
        return (
            f"====== Parameter {self.name}\n"
            f"       DataType: {self.data_type}\n"
            f"       Value: {self.value}\n"
            f"       Vary: {self.vary}\n"
            f"       Input source: {self.input_source}\n"
        )


@dataclass
class GeneralConfig:
    interactive: bool = True
    output_directory: Path = Path("./out_dir")
    # This forces every run to be reproducible by default
    random_seed: int = 0
    workflow: Workflow = Workflow.PFLOTRAN

    def override_with(self, other: "GeneralConfig"):
        self.interactive = other.interactive
        self.output_directory = other.output_directory
        self.random_seed = other.random_seed
        self.workflow = other.workflow

    @staticmethod
    def from_dict(conf: dict[str, Any]) -> "GeneralConfig":
        result = GeneralConfig()

        if conf == {}:
            return result

        interactive = conf.pop("interactive", None)
        if interactive is not None:
            if not isinstance(interactive, bool):
                raise ValueError("`interactive` is not of type bool")
            result.interactive = interactive

        output_directory = conf.pop("output_directory", None)
        if output_directory is not None:
            if isinstance(output_directory, str):
                output_directory = Path(output_directory)
            if not isinstance(output_directory, Path):
                raise ValueError("`output_directory` is not anything path-like")
            result.output_directory = output_directory

        random_seed = conf.pop("random_seed", None)
        if random_seed is not None:
            if not isinstance(random_seed, int):
                raise ValueError("`random_seed` is not of type int")
            result.random_seed = random_seed

        workflow = conf.pop("workflow", None)
        if workflow is not None:
            if isinstance(workflow, str):
                workflow = Workflow(workflow)
            if not isinstance(workflow, Workflow):
                raise ValueError("`workflow` is not of type Workflow")
            result.workflow = workflow

        if conf:
            raise ValueError(f"There was additional data in config dict: {conf}")

        return result

    def __str__(self) -> str:
        return (
            f"=== GeneralConfig\n"
            f"    Interactive: {self.interactive}\n"
            f"    Output directory: {self.output_directory}\n"
            f"    Random seed: {self.random_seed}\n"
            f"    Using workflow: {self.workflow}\n"
        )


@dataclass
class Config:
    # Need to use field here, as otherwise it would be the same dict across several objects
    general: GeneralConfig = field(default_factory=lambda: GeneralConfig())
    steps: list[str] = field(default_factory=lambda: ["global"])
    parameters: dict[str, Parameter] = field(default_factory=lambda: {})
    data: dict[str, Any] = field(default_factory=lambda: {})

    def override_with(self, other_config: "Config"):
        self.general = other_config.general
        self.steps = other_config.steps or self.steps
        self.parameters |= other_config.parameters
        self.data |= other_config.data

    @staticmethod
    def from_dict(conf: dict[str, Any]) -> "Config":
        result = Config()

        if conf == {}:
            return result

        general = conf.pop("general", None)
        if general is not None:
            result.general = GeneralConfig.from_dict(general)

        steps = conf.pop("steps", None)
        if steps is not None:
            if not isinstance(steps, list):
                raise ValueError("`steps` is not of type list[str]")

            if len(steps) < 1:
                raise ValueError("`steps` must contain at least one entry")

            for item in steps:
                if not isinstance(item, str):
                    raise ValueError("`steps` is not of type list[str]")

            result.steps = steps

        parameters = conf.pop("parameters", None)
        if parameters is not None:
            if not isinstance(parameters, dict):
                raise ValueError("`parameters` is not of type dict")
            typed_parameters = {}
            for param_name, param_meta in parameters.items():
                typed_parameters[param_name] = Parameter.from_dict(param_name, param_meta)

            result.parameters = typed_parameters

        if conf.pop("general", None) is not None:
            raise ValueError("`data` must not be given via a config file")

        if conf:
            raise ValueError(f"There was additional data in config dict: {conf}")

        return result

    @staticmethod
    def from_yaml(config_file_path: str) -> "Config":
        logging.debug("Trying to load config from %s", config_file_path)
        try:
            with open(config_file_path, encoding="utf-8") as config_file:
                yaml_values = yaml.load(config_file)
        except OSError as err:
            logging.error("Could not find config file '%s', %s", config_file_path, err)
            raise err
        logging.debug("Loaded config from %s", config_file_path)
        logging.debug("Yaml: %s", yaml_values)

        return Config.from_dict(yaml_values)

    def __str__(self) -> str:
        parameter_strings = []
        for name, param in self.parameters.items():
            parameter_strings.append(str(param))

        return (
            f"=== This config will be used ===\n"
            f"\n"
            f"{self.general}\n"
            f"=== Steps (in this order)\n"
            f"    {"\n".join(self.steps)}\n"
            f"\n"
            f"=== Parameters\n\n"
            f"{"\n".join(parameter_strings)}"
            f"\n"
        )


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
    run_config.general.interactive = not arguments.non_interactive
    if arguments.non_interactive:
        logging.debug("Running non-interactively")

    logging.debug("Config: %s", run_config)

    return run_config
