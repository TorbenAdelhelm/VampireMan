import argparse
import datetime
import enum
import logging
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from ruamel.yaml import YAML

yaml = YAML(typ="safe")


class DataType(enum.StrEnum):
    # XXX is this even needed?
    SCALAR = "scalar"
    ARRAY = "array"
    STRUCT = "structure"
    # This needs to be a dict with the keys `frequency`, `max` and `min`
    PERLIN = "perlin"
    # This needs `location`, `injection_temp` and `injection_rate`
    HEATPUMP = "heatpump"


class Distribution(enum.StrEnum):
    UNIFORM = "uniform"
    LOG = "logarithmic"


class Vary(enum.StrEnum):
    NONE = "none"
    CONST = "const_within_datapoint"
    TIME = "timely_vary_within_datapoint"
    SPACE = "spatially_vary_within_datapoint"


class InputSource(enum.StrEnum):
    MANUAL = "manual"


class Workflow(enum.StrEnum):
    PFLOTRAN = "pflotran"


class HeatPump(BaseModel):
    location: list[float]
    # TODO make this list[float]
    injection_temp: float
    # TODO make this list[float]
    injection_rate: float


class Parameter(BaseModel):
    name: str
    data_type: DataType
    value: float | list[int] | HeatPump | dict[str, float | list[float]]
    # steps: list[str]
    distribution: Distribution = Distribution.UNIFORM
    vary: Vary = Vary.NONE
    input_source: InputSource = InputSource.MANUAL  # TODO is this really needed?

    def __str__(self) -> str:
        return (
            f"====== Parameter {self.name}\n"
            f"       DataType: {self.data_type}\n"
            f"       Value: {self.value}\n"
            f"       Distribution: {self.distribution}\n"
            f"       Vary: {self.vary}\n"
            f"       Input source: {self.input_source}\n"
        )


class Data(BaseModel):
    name: str
    data_type: DataType
    value: int | float | list[int] | list[float] | HeatPump | Any  # | np.ndarray

    def __str__(self) -> str:
        return f"====== {self.name} [{self.data_type}]: {self.value}"


class Datapoint(BaseModel):
    index: int
    data: dict[str, Data]

    def __str__(self) -> str:
        data_strings = []
        for _, item in self.data.items():
            data_strings.append(str(item))

        return f"=== Datapoint #{self.index}:\n" f"{"\n".join(data_strings)}"


class GeneralConfig(BaseModel):
    number_cells: list[int] = Field(default_factory=lambda: [32, 128, 1])
    cell_resolution: list[float] = Field(default_factory=lambda: [5.0, 5.0, 5.0])
    interactive: bool = True
    # XXX: Hopefully the format `2024-08-17T10:06:15+00:00` is supported by the common file systems
    output_directory: Path = Path(f"./datasets_out/{datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")}")
    # This forces every run to be reproducible by default
    random_seed: None | int = 0
    number_datapoints: int = 1
    workflow: Workflow = Workflow.PFLOTRAN
    profiling: bool = False

    def __str__(self) -> str:
        return (
            f"=== GeneralConfig\n"
            f"    Interactive: {self.interactive}\n"
            f"    Output directory: {self.output_directory}\n"
            f"    Random seed: {self.random_seed}\n"
            f"    Number of datapoints: {self.number_datapoints}\n"
            f"    Using workflow: {self.workflow}\n"
        )


class Config(BaseModel):
    # Need to use field here, as otherwise it would be the same dict across several objects
    # fluidsimulation hat man immer: zeit, solver
    general: GeneralConfig = Field(default_factory=lambda: GeneralConfig())
    steps: list[str] = Field(default_factory=lambda: ["global"])
    # boundary conditions, maybe time??
    parameters: dict[str, Parameter] = Field(default_factory=lambda: {})
    # TODO split this in datapoints_fixed, datapoint_const_within_datapoint, ...
    datapoints: list[Datapoint] = Field(default_factory=lambda: [])
    _rng: np.random.Generator = np.random.default_rng(seed=0)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    def put_parameter_name_into_data(cls, data):
        """This "validator" only copies the name of a parameter into the dict so it is accessible"""
        for name, parameter in data.get("parameters", {}).items():
            parameter["name"] = name
        return data

    @model_validator(mode="after")
    def instantiate_random_number_generator(self):
        """This "validator" instantiates the global rng"""
        self._rng = np.random.default_rng(seed=self.general.random_seed)
        return self

    @field_validator("steps")
    def non_empty_list(cls, value):
        if not isinstance(value, list) or len(value) == 0:
            raise ValueError("`steps` must be a non-empty list")
        return value

    def override_with(self, other_config: "Config"):
        self.general = other_config.general
        self.steps = other_config.steps or self.steps
        self.parameters |= other_config.parameters
        self.datapoints = other_config.datapoints

    def get_rng(self) -> np.random.Generator:
        return self._rng

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

        return Config(**yaml_values)

    def __str__(self) -> str:
        parameter_strings = []
        for _, param in self.parameters.items():
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


def load_config(arguments: argparse.Namespace, workflow_module: ModuleType) -> Config:
    run_config = workflow_module.get_defaults()

    # Load config from file if provided
    config_file = arguments.config_file
    if config_file is not None:
        user_config = Config.from_yaml(config_file)
        run_config.override_with(user_config)

    # Also consider arguments from command line
    run_config.general.interactive = not arguments.non_interactive
    if arguments.non_interactive:
        logging.debug("Running non-interactively")

    if arguments.datapoints is not None:
        run_config.general.number_datapoints = int(arguments.datapoints)

    logging.debug("Config: %s", run_config)

    return run_config
