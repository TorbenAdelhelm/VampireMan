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

from .utils import profile_function

yaml = YAML(typ="safe")


class DataType(enum.StrEnum):
    # XXX is this even needed?
    SCALAR = "scalar"
    ARRAY = "array"
    # This needs to be a dict with the keys `frequency`, `max` and `min`
    PERLIN = "perlin"
    # This needs `location`, `injection_temp` and `injection_rate`
    HEATPUMP = "heatpump"
    HEATPUMPS = "heatpumps"
    FILE = "file"


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


class Parameter(BaseModel):
    name: str
    data_type: DataType
    value: str | float | list[int] | HeatPump | dict[str, float | list[float]]
    # steps: list[str]
    distribution: Distribution = Distribution.UNIFORM
    vary: Vary = Vary.FIXED

    @model_validator(mode="after")
    def str_value_if_file_datatype(self):
        if (isinstance(self.value, str) and not self.data_type == DataType.FILE) or (
            self.data_type == DataType.FILE and not isinstance(self.value, str)
        ):
            raise ValueError("Only when input is a file, the value may be a str")
        return self

    def __str__(self) -> str:
        return (
            f"====== Parameter {self.name}\n"
            f"       DataType: {self.data_type}\n"
            f"       Value: {self.value}\n"
            f"       Distribution: {self.distribution}\n"
            f"       Vary: {self.vary}\n"
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
    hydrogeological_parameters: dict[str, Parameter] = Field(default_factory=lambda: {})
    heatpump_parameters: dict[str, Parameter] = Field(default_factory=lambda: {})
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


def get_defaults() -> Config:
    config = Config()

    config.hydrogeological_parameters["permeability"] = Parameter(
        name="permeability",
        data_type=DataType.SCALAR,
        value=1.2882090745857623e-10,
        vary=Vary.SPACE,
    )
    config.hydrogeological_parameters["temperature"] = Parameter(
        name="temperature",
        data_type=DataType.SCALAR,
        value=10.6,
    )
    config.hydrogeological_parameters["pressure"] = Parameter(
        name="pressure",
        data_type=DataType.SCALAR,
        vary=Vary.CONST,
        value=-0.0024757478454929577,
    )
    config.heatpump_parameters["hp1"] = Parameter(
        name="hp1",
        data_type=DataType.HEATPUMP,
        value=HeatPump(location=[16, 32, 1], injection_temp=13.6, injection_rate=0.00024),
    )

    return config


def ensure_parameter_correct(parameter: Parameter):
    pressure_correct = True
    if parameter.data_type == DataType.ARRAY:
        try:
            if not (
                isinstance(parameter.value, dict)
                and isinstance(parameter.value["min"], float)
                and isinstance(parameter.value["max"], float)
            ):
                pressure_correct = False
        except KeyError:
            pressure_correct = False
        if not pressure_correct:
            raise ValueError(f"`{parameter.name}` doesn't have min or max values that are floats")


@profile_function
def ensure_config_is_valid(config: Config) -> Config:
    # TODO make this more extensive

    pressure = config.hydrogeological_parameters.get("pressure")
    permeability = config.hydrogeological_parameters.get("permeability")
    temperature = config.hydrogeological_parameters.get("temperature")

    # These hydrogeological parameters are mandatory
    for name, item in [
        ("pressure", pressure),
        ("permeability", permeability),
        ("temperature", temperature),
    ]:
        if item is None:
            raise ValueError(f"`{name}` must not be None")

    assert pressure is not None
    assert permeability is not None
    assert temperature is not None

    if (DataType.FILE in (pressure.data_type, permeability.data_type)) and pressure.data_type != permeability.data_type:
        raise ValueError("If one of `pressure`, `permeability` is a file, all must be a file")

    ensure_parameter_correct(pressure)

    # Simulation without heatpumps doesn't make much sense
    heatpumps = [{name: d.name} for name, d in config.heatpump_parameters.items() if d.data_type == DataType.HEATPUMP]
    if len(heatpumps) < 1:
        logging.error("There are no heatpumps in this simulation. This usually doesn't make much sense.")

    return config


def load_config(arguments: argparse.Namespace, workflow_module: ModuleType) -> Config:
    run_config = get_defaults()

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
