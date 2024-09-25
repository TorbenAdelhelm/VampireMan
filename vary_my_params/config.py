import argparse
import datetime
import enum
import logging
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, FilePath, field_validator, model_validator
from ruamel.yaml import YAML

from .utils import profile_function

yaml = YAML(typ="safe")


class Distribution(enum.StrEnum):
    UNIFORM = "uniform"
    LOG = "logarithmic"


class Vary(enum.StrEnum):
    FIXED = "fixed"
    CONST = "const_within_datapoint"
    TIME = "timely_vary_within_datapoint"
    SPACE = "spatially_vary_within_datapoint"


class Workflow(enum.StrEnum):
    PFLOTRAN = "pflotran"


class TimeToSimulate(BaseModel):
    final_time: float = 27.5
    unit: str = "year"

    def __str__(self) -> str:
        return f"{self.final_time} [{self.unit}]"


class HeatPump(BaseModel):
    location: list[float]
    # TODO make this list[float]
    injection_temp: float
    # TODO make this list[float]
    injection_rate: float


class HeatPumps(BaseModel):
    number: int
    injection_temp_min: float
    injection_temp_max: float
    injection_rate_min: float
    injection_rate_max: float


class ParameterValuePerlin(BaseModel):
    frequency: list[float]
    max: float
    min: float

    @model_validator(mode="after")
    def frequency_len_three(self):
        if len(self.frequency) != 3:
            raise ValueError("`frequency` must have exactly three values")
        return self

    @model_validator(mode="after")
    def ensure_max_ge_min(self):
        if self.max < self.min:
            raise ValueError("`max` value must be greater or equal to `min`")
        return self


class ParameterValueMinMax(BaseModel):
    min: float
    max: float

    @model_validator(mode="after")
    def ensure_max_ge_min(self):
        if self.max < self.min:
            raise ValueError("`max` value must be greater or equal to `min`")
        return self


class Parameter(BaseModel):
    name: str
    value: float | list[int] | HeatPumps | HeatPump | ParameterValuePerlin | ParameterValueMinMax | FilePath
    # steps: list[str]
    distribution: Distribution = Distribution.UNIFORM
    vary: Vary = Vary.FIXED

    def __str__(self) -> str:
        return (
            f"====== Parameter {self.name}\n"
            f"       type(): {type(self.value)}\n"
            f"       Value: {self.value}\n"
            f"       Distribution: {self.distribution}\n"
            f"       Vary: {self.vary}\n"
        )


class Data(BaseModel):
    name: str
    value: int | float | list[int] | list[float] | HeatPump | Any  # | np.ndarray

    def __str__(self) -> str:
        value = "ndarray" if isinstance(self.value, np.ndarray) else self.value
        return f"====== {self.name} [{type(self.value)}]: {value}"


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
    # XXX: distance to border in percent?
    interactive: bool = True
    # XXX: Hopefully the format `2024-08-17T10:06:15+00:00` is supported by the common file systems
    output_directory: Path = Path(f"./datasets_out/{datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")}")
    # This forces every run to be reproducible by default
    random_seed: None | int = 0
    number_datapoints: int = 1
    time_to_simulate: TimeToSimulate = Field(default_factory=lambda: TimeToSimulate())
    workflow: Workflow = Workflow.PFLOTRAN
    profiling: bool = False

    # This makes pydantic fail if there is extra data in the yaml config file that cannot be parsed
    model_config = ConfigDict(extra="forbid")

    def __str__(self) -> str:
        return (
            f"=== GeneralConfig\n"
            f"    Interactive: {self.interactive}\n"
            f"    Output directory: {self.output_directory}\n"
            f"    Random seed: {self.random_seed}\n"
            f"    Number of datapoints: {self.number_datapoints}\n"
            f"    Using workflow: {self.workflow}\n"
            f"    Number of cells: {self.number_cells}\n"
            f"    Cell resolution: {self.cell_resolution}\n"
            f"    Time to simulate: {str(self.time_to_simulate)}\n"
            f"    Profiling: {self.profiling}\n"
        )


class Config(BaseModel):
    # Need to use field here, as otherwise it would be the same dict across several objects
    general: GeneralConfig = Field(default_factory=lambda: GeneralConfig())
    steps: list[str] = Field(default_factory=lambda: ["global"])
    hydrogeological_parameters: dict[str, Parameter] = Field(
        default_factory=lambda: {
            "permeability": Parameter(
                name="permeability",
                vary=Vary.SPACE,
                value=1.2882090745857623e-10,
            ),
            "pressure": Parameter(
                name="pressure",
                vary=Vary.FIXED,
                value=-0.0024757478454929577,
            ),
            "temperature": Parameter(
                name="temperature",
                value=10.6,
            ),
        }
    )
    heatpump_parameters: dict[str, Parameter] = Field(
        default_factory=lambda: {
            "hp1": Parameter(
                name="hp1",
                value=HeatPump(
                    location=[16, 32, 1],
                    injection_temp=13.6,
                    injection_rate=0.00024,
                ),
            )
        }
    )
    # TODO split this in datapoints_fixed, datapoint_const_within_datapoint, ...
    datapoints: list[Datapoint] = Field(default_factory=lambda: [])
    _rng: np.random.Generator = np.random.default_rng(seed=0)

    # This makes pydantic fail if there is extra data in the yaml config file that cannot be parsed
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    def put_parameter_name_into_data(cls, data):
        """This "validator" only copies the name of a parameter into the dict so it is accessible"""
        for name, parameter in data.get("hydrogeological_parameters", {}).items():
            parameter["name"] = name
        for name, parameter in data.get("heatpump_parameters", {}).items():
            parameter["name"] = name
        return data

    @model_validator(mode="after")
    def instantiate_random_number_generator(self):
        """This "validator" instantiates the global rng"""
        self._rng = np.random.default_rng(seed=self.general.random_seed)
        return self

    @model_validator(mode="after")
    def check_all_or_none_file_paths(self):
        """Check if one parameter is a file, then all must be"""

        # Get all parameters
        permeability = self.hydrogeological_parameters.get("permeability", False)
        pressure = self.hydrogeological_parameters.get("pressure", False)
        temperature = self.hydrogeological_parameters.get("temperature", False)

        # Override with True where value is a Path to a file
        if permeability:
            permeability = isinstance(permeability, Path)
        if pressure:
            pressure = isinstance(pressure, Path)
        if temperature:
            temperature = isinstance(temperature, Path)

        # If any of the parameters is True, all must be. Otherwise if none is True, its also fine
        if not (permeability == pressure == temperature):
            raise ValueError(
                "If any of the parameters `permeability`, `pressure` or `temperature` is a Path, all must be"
            )

        return self

    @field_validator("steps")
    def non_empty_list(cls, value):
        if not isinstance(value, list) or len(value) == 0:
            raise ValueError("`steps` must be a non-empty list")
        return value

    def override_with(self, other_config: "Config"):
        self.general = other_config.general
        self.steps = other_config.steps or self.steps
        self.hydrogeological_parameters |= other_config.hydrogeological_parameters
        self.heatpump_parameters |= other_config.heatpump_parameters
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
        for _, param in self.hydrogeological_parameters.items():
            parameter_strings.append(str(param))
        for _, param in self.heatpump_parameters.items():
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


@profile_function
def ensure_config_is_valid(config: Config) -> Config:
    # TODO make this more extensive

    pressure = config.hydrogeological_parameters.get("pressure")
    permeability = config.hydrogeological_parameters.get("permeability")
    temperature = config.hydrogeological_parameters.get("temperature")

    if permeability is None:
        raise ValueError("`permeability` must not be None")
    if pressure is None:
        raise ValueError("`pressure` must not be None")
    if temperature is None:
        raise ValueError("`temperature` must not be None")

    # Simulation without heatpumps doesn't make much sense
    heatpumps = [{name: d.name} for name, d in config.heatpump_parameters.items() if isinstance(d.value, HeatPump)]
    heatpumps_gen = [{name: d.name} for name, d in config.heatpump_parameters.items() if isinstance(d.value, HeatPumps)]
    if len(heatpumps) + len(heatpumps_gen) < 1:
        logging.error("There are no heatpumps in this simulation. This usually doesn't make much sense.")

    return config


def load_config(arguments: argparse.Namespace) -> Config:
    run_config = Config()

    # Load config from file if provided
    config_file = arguments.config_file
    if config_file is not None:
        user_config = Config.from_yaml(config_file)
        run_config.override_with(user_config)

    # Also consider arguments from command line
    if arguments.non_interactive:
        run_config.general.interactive = False

    if run_config.general.interactive:
        logging.info("Running non-interactively")

    logging.debug("Resulting config of load_config: %s", run_config)

    return run_config
