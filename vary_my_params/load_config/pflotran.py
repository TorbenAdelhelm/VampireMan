import logging

from ..config import Config, DataType, HeatPump, Parameter, Vary


def get_defaults() -> Config:
    config = Config()

    config.parameters["permeability"] = Parameter(
        name="permeability",
        data_type=DataType.SCALAR,
        value=1.2882090745857623e-10,
        vary=Vary.SPACE,
    )
    config.parameters["temperature"] = Parameter(
        name="temperature",
        data_type=DataType.SCALAR,
        value=10.6,
    )
    config.parameters["hp1"] = Parameter(
        name="hp1",
        data_type=DataType.HEATPUMP,
        value=HeatPump(location=[16, 32, 1], injection_temp=13.6, injection_rate=0.00024),
    )

    return config


def ensure_parameter_isset(config: Config, name: str):
    value = config.parameters.get(name)
    if value is None:
        raise ValueError(f"`{name}` must not be None")


def ensure_config_is_valid(config: Config):
    # TODO make this more extensive

    # These parameters are mandatory
    for item in [
        "permeability",
    ]:
        ensure_parameter_isset(config, item)

    # Simulation without heatpumps doesn't make much sense
    heatpumps = [{name: d.name} for name, d in config.parameters.items() if d.data_type == DataType.HEATPUMP]
    if len(heatpumps) < 1:
        logging.warn("There are no heatpumps in this simulation. This usually doesn't make much sense.")
