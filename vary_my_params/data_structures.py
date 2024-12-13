"""This file holds all data structures that are used throughout the software."""

# ruff: noqa: F722
import datetime
import enum
import inspect
import logging
from pathlib import Path

import numpy as np
from numpydantic import NDArray, Shape
from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator, model_validator
from ruamel.yaml import YAML

yaml = YAML(typ="safe")


def value_is_3d(value: list[float] | NDArray):
    """Ensure value is given in three dimensional space."""
    if len(value) == 2:  # pyright: ignore
        if isinstance(value, NDArray):  # pyright: ignore
            value = np.append(value, 1)  # pyright: ignore
        else:
            value.append(1)  # pyright: ignore

    if len(value) != 3:  # pyright: ignore
        raise ValueError("Value must be given in three dimensional space")

    return value


class Distribution(enum.StrEnum):
    UNIFORM = "uniform"
    LOG = "logarithmic"


class Vary(enum.StrEnum):
    """This represents the vary mode of `Parameter.vary`."""

    FIXED = "fixed"
    """Don't vary the `Parameter` at all. Variation stage simply takes `Parameter.value` and copy it over to the
    `Data` item in the `Datapoint`.
    """

    CONST = "const_within_datapoint"
    """The `Parameter` will be varied constantly within the `Datapoint`, so the `Parameter.value` won't change
    within this `Datapoint`. The value will, however, be varied across the whole datasets, i.e.,
    `State.datapoints`.
    """

    SPACE = "spatially_vary_within_datapoint"
    """`Parameter.value` will be varied spatially within the `Datapoint` and also across the dataset. E.g., this
    could be the permeability that varies within the `Datapoint` with a perlin noise function.
    """


class Workflow(enum.StrEnum):
    """Enum behind `GeneralConfig.workflow`."""

    PFLOTRAN = "pflotran"
    """The reference implementation and therefore the default workflow."""


class TimeToSimulate(BaseModel):
    """The timespan that the simulation tool should simulate. Value and unit are separated for more flexibility."""

    final_time: float = 27.5
    """Value component."""

    unit: str = "year"
    """The default unit is `year`, so when the value is omitted in the settings file, years is assumed. Using SI units
    here doesn't make much sense as we are unlikely to simulate anything other than years."""

    model_config = ConfigDict(extra="forbid")

    def __str__(self) -> str:
        """Returns time including unit, e.g., `27.5 [year]`."""
        return f"{self.final_time} {self.unit}"


class ParameterValueMinMax(BaseModel):
    """Datastructure to represent a `min` and a `max` value for `Parameter.value`."""

    min: float
    max: float

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def ensure_max_ge_min(self):
        """Ensure the `min` value is smaller or equal to the `max` value."""
        if self.max < self.min:
            raise ValueError("`max` value must be greater or equal to `min`")
        return self


class TimeBasedValue(BaseModel):
    """This represents a time based value. This could be anything that can be varied in the `Vary.TIME` mode."""

    time_unit: str = "year"
    """The unit of each of the float values in the `values` dict."""

    values: dict[float, ParameterValueMinMax | float]
    """Values that represent timesteps and their respective values. E.g., `{0: 10, 1: 15}` means, that at
    timestep `0`, the value is `10` and at timestep `1` the value is `15`.
        """


class HeatPump(BaseModel):
    """Datastructure representing a single heat pump. A heat pump has a location, an injection temperature and an
    injection rate."""

    location: list[float]
    """The location where the `HeatPump` should be. It is given in cells, the program translates the cell-based location
    into coordinates matching the domain by multiplying it by the `GeneralConfig.cell_resolution`."""

    # TODO make this list[float]
    injection_temp: TimeBasedValue | ParameterValueMinMax | float
    """The injection temperature of the `HeatPump` in degree Celsius."""

    # TODO make this list[float]
    injection_rate: TimeBasedValue | ParameterValueMinMax | float
    """The injection rate of the `HeatPump` in m^3/s."""

    model_config = ConfigDict(extra="forbid")

    _validated_3d = field_validator("location")(value_is_3d)


class HeatPumps(BaseModel):
    """Datastructure representing a set of heat pumps. During the `vary_my_params.pipeline.prepare_parameters` stage,
    the individual `HeatPump`s will be generated from this.

    Using `State.get_rng`, values between min and max are chosen for each of the generated `HeatPump`s.
    """

    number: PositiveInt
    """How many `HeatPump`s to generate."""

    injection_temp: TimeBasedValue | ParameterValueMinMax
    injection_rate: TimeBasedValue | ParameterValueMinMax

    model_config = ConfigDict(extra="forbid")


class ParameterValuePerlin(BaseModel):
    """Datastructure to represent a perlin noise value for `Parameter.value`."""

    frequency: ParameterValueMinMax | list[float]
    """The larger these values are, the more fine grained the perlin field will
    be (i.e., the smaller the "dots" are and how many of them).

    Can either be a fixed three dimensional list of floats, in which case the value will simply be taken as is,
    or `ParameterValueMinMax`, in which case the min and max values describe a range in which three floats are
    being generated.
    """

    max: float
    min: float

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def ensure_3d_if_list(self):
        """If frequency is a list, check if it is 3d"""
        if isinstance(self.frequency, list):
            value_is_3d(self.frequency)
        return self

    @model_validator(mode="after")
    def ensure_max_ge_min(self):
        """Ensure the `min` value is smaller or equal to the `max` value."""
        if self.max < self.min:
            raise ValueError("`max` value must be greater or equal to `min`")
        return self


class ValueXYZ(BaseModel):
    """Datastructure to represent a vector of three float values."""

    x: float
    y: float
    z: float

    model_config = ConfigDict(extra="forbid")

    def __str__(self) -> str:
        # This "hack" is needed as there is some problem when serializing otherwise
        if inspect.stack()[1].function == "model_dump_json":
            return {"x": self.x, "y": self.y, "z": self.z}  # pyright: ignore
        return super().__str__()


class Parameter(BaseModel):
    name: str
    value: (
        float
        | list[int]
        | HeatPumps
        | HeatPump
        | ParameterValuePerlin
        | ParameterValueMinMax
        | Path  # Could use pydantic.FilePath here, but then tests fail as cwd does not match
        | ValueXYZ
        | NDArray[Shape["*, ..."], (np.float64,)]  # pyright: ignore
    )
    distribution: Distribution = Distribution.UNIFORM
    vary: Vary = Vary.FIXED

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # XXX: Store this in the parameter?
    # _datapoints: dict[int, Data]
    #
    # def set_datapoint(self, index: int, data: Data):
    #     self._datapoints[index] = data

    @field_validator("value")
    @classmethod
    def make_path(cls, value):
        """If NDArray is of type path, make it a Path"""
        if isinstance(value, np.ndarray) and value.ndim == 0:
            return Path(str(value))

        return value

    def __str__(self) -> str:
        return (
            f"====== Parameter {self.name}\n"
            f"       Distribution: {self.distribution}\n"
            f"       Vary: {self.vary}\n"
            f"       type(): {type(self.value)}\n"
            f"       Value: {self.value}\n"
        )


class Data(BaseModel):
    name: str
    value: int | float | list[int] | list[float] | HeatPump | ValueXYZ | NDArray

    model_config = ConfigDict(extra="forbid")

    def __str__(self) -> str:
        value = "ndarray" if isinstance(self.value, np.ndarray) else self.value
        return f"====== {self.name} [{type(self.value)}]: {value}"


class Datapoint(BaseModel):
    index: int
    data: dict[str, Data]

    model_config = ConfigDict(extra="forbid")

    def __str__(self) -> str:
        data_strings = []
        for _, item in self.data.items():
            data_strings.append(str(item))

        return f"=== Datapoint #{self.index}:\n" f"{"\n".join(data_strings)}"


class GeneralConfig(BaseModel):
    """The `GeneralConfig` doesn't change during execution of the program."""

    number_cells: NDArray[Shape["3 number_cells"], int] | NDArray[Shape["2 number_cells"], int] = Field(  # pyright: ignore[reportInvalidTypeArguments]
        default_factory=lambda: np.array([32, 256, 1])
    )
    """Specifies the number of cells for the simulation."""

    cell_resolution: float = 5.0
    """Resolution of each of the cells. Cells must be cubic currently."""

    shuffle_datapoints: bool = False
    """Whether or not to shuffle the order the calculated data from each parameter appears in the datapoints."""

    interactive: bool = True
    """Whether or not to run interactively. Setting this to `False` is useful in a CI or an unattended run on an HPC
    Cluster.

    When running in interactive mode, the execution halts between each of the selected stages and asks the user for
    confirmation to proceed. Also, if any expected problems occur during execution, e.g., the `pflotran.h5` file is
    already present, the user is asked what to do.

    When running in non-interactive mode, like a `--force` option, data loss can happen.
    """

    output_directory: Path = Path(f"./datasets_out/{datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")}")
    """The directory to output the generated datasets. Will be created if not existing.

    The default is in the format `2024-08-17T10:06:15+00:00` and is hopefully supported by the common file systems.
    """

    # This forces every run to be reproducible by default
    random_seed: None | int = 0
    """This random seed will be passed to the numpy random number generator. By default the value is 0, meaning that a
    given set of input parameters (read from a settings file) always produces the same outputs. If the used simulation
    tool is deterministic, then the same inputs yield the same simulation results.

    Setting this to another fixed value will yield (still deterministic) different results.

    Setting this value to `None`, or rather `null` in a yaml settings file, will always use a random value for the
    random seed, making it nondeterministic.
    """

    number_datapoints: PositiveInt = 1
    """The number of datapoints to be generated."""

    time_to_simulate: TimeToSimulate = Field(default_factory=lambda: TimeToSimulate())
    """Influences the timespan of the simulation."""

    workflow: Workflow = Workflow.PFLOTRAN
    """In essence, this states which simulation tool specific functions should be called during later stages of the
    pipeline."""

    profiling: bool = False
    """If set to `True`, the stages are being profiled and `profiling_<stagename>.txt` files are being written in the
    root of the project. Also, the execution time of the stages are logged. This can help during development but is
    probably not something a user of the program should use."""

    mpirun: bool = True
    """If the simulation tool should be called by running `mpirun -n x <simulationtool>` or simply
    `<simulationtool>`."""

    mpirun_procs: PositiveInt = 1
    """When `mpirun` is set to `True`, specifies the number of ranks being used, i.e. the `x` in `mpirun -n x
    <simulationtool>`."""

    mute_simulation_output: bool = False
    """Some simulation tools produce output that can be muted. This option disables the output."""

    # XXX: distance to border in percent?

    # This makes pydantic fail if there is extra data in the yaml settings file that cannot be parsed
    model_config = ConfigDict(extra="forbid")

    _validated_3d = field_validator("number_cells")(value_is_3d)

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


class State(BaseModel):
    # Need to use field here, as otherwise it would be the same dict across several objects
    general: GeneralConfig = Field(default_factory=lambda: GeneralConfig())
    """The `GeneralConfig`."""

    pure: bool = Field(True, exclude=True)
    """Internally used to detect if anything runs impure/non-deterministically."""

    hydrogeological_parameters: dict[str, Parameter] = Field(
        default_factory=lambda: {
            "permeability": Parameter(
                name="permeability",
                vary=Vary.FIXED,
                value=1.2882090745857623e-10,
            ),
            "hydraulic_head": Parameter(
                name="hydraulic_head",
                vary=Vary.FIXED,
                value=-0.0024757478454929577,
            ),
            "temperature": Parameter(
                name="temperature",
                vary=Vary.FIXED,
                value=10.6,
            ),
        }
    )
    heatpump_parameters: dict[str, Parameter] = Field(
        default_factory=lambda: {
            "hp1": Parameter(
                name="hp1",
                vary=Vary.FIXED,
                value=HeatPump(
                    location=[16, 32, 1],
                    injection_temp=13.6,
                    injection_rate=0.00024,
                ),
            )
        }
    )
    """This defines the default `heatpump_parameters`. It creates a single heat pump. IMPORTANT: if given a user
    settings file that specifies heat pump `hp2` and `hp3`, the `hp1` from the defaults will get discarded! If `hp1`
    should be used when there are other heat pumps, it must be specified along the others in the settings file.
    """

    # TODO split this in datapoints_fixed, datapoint_const_within_datapoint, ...
    datapoints: list[Datapoint] = Field(default_factory=lambda: [])

    _rng: np.random.Generator = np.random.default_rng(seed=0)
    """The execution wide random number generator."""

    # This makes pydantic fail if there is extra data in the yaml settings file that cannot be parsed
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
        permeability = self.hydrogeological_parameters.get("permeability")
        hydraulic_head = self.hydrogeological_parameters.get("hydraulic_head")
        temperature = self.hydrogeological_parameters.get("temperature")

        # Override with True where value is a Path to a file
        if permeability is not None and isinstance(permeability.value, Path):
            if not permeability.vary == Vary.FIXED:
                raise ValueError("When providing a Path, vary mode must be FIXED")
            permeability = True
        else:
            permeability = False
        if hydraulic_head is not None and isinstance(hydraulic_head.value, Path):
            if not hydraulic_head.vary == Vary.FIXED:
                raise ValueError("When providing a Path, vary mode must be FIXED")
            hydraulic_head = True
        else:
            hydraulic_head = False
        if temperature is not None and isinstance(temperature.value, Path):
            if not temperature.vary == Vary.FIXED:
                raise ValueError("When providing a Path, vary mode must be FIXED")
            temperature = True
        else:
            temperature = False

        # If any of the parameters is True, all must be. Otherwise if none is True, its also fine
        if not (permeability == hydraulic_head == temperature):
            raise ValueError(
                "If any of the parameters `permeability`, `hydraulic_head` or `temperature` is a Path, all must be"
            )

        return self

    @model_validator(mode="before")
    def prevent_pure_field_to_be_set(cls, data):
        """This prevents setting the pure property."""
        if data.get("pure") is not None:
            raise ValueError("Not allowed to specify `pure` parameter.")
        return data

    def override_with(self, other_state: "State"):
        """Override this `State` with another given `State` object. Will discard current `GeneralConfig`, current
        `heatpump_parameters`, and `datapoints`, but will merge `hydrogeological_parameters`.
        """
        self.general = other_state.general
        self.hydrogeological_parameters |= other_state.hydrogeological_parameters
        self.heatpump_parameters = other_state.heatpump_parameters
        self.datapoints = other_state.datapoints

    def get_rng(self) -> np.random.Generator:
        """Returns the execution-wide same instance of the random number generator instantiated with
        `GeneralConfig.random_seed`. If using randomness of any kind, the rng returned by this function should be used
        to make results as reproducible as possible."""
        return self._rng

    @staticmethod
    def from_yaml(settings_file_path: str) -> "State":
        logging.debug("Trying to load config from %s", settings_file_path)
        try:
            with open(settings_file_path, encoding="utf-8") as state_file:
                yaml_values = yaml.load(state_file)
        except OSError as err:
            logging.error("Could not open settings file '%s', %s", settings_file_path, err)
            raise err
        logging.debug("Loaded state from %s", settings_file_path)
        logging.debug("Yaml: %s", yaml_values)

        return State(**yaml_values)

    def __str__(self) -> str:
        parameter_strings = []
        for _, parameter in (self.hydrogeological_parameters | self.heatpump_parameters).items():
            parameter_strings.append(str(parameter))

        return (
            f"=== This state will be used ===\n"
            f"\n"
            f"{self.general}\n"
            f"=== Parameters\n\n"
            f"{"\n".join(parameter_strings)}"
            f"\n"
        )
