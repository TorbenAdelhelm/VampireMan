from ..config import Config, DataType, Parameter, Vary


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

    return config


def ensure_parameter_isset(config: Config, name: str):
    value = config.parameters.get(name)
    if value is None:
        raise ValueError(f"`{name}` must not be None")


def ensure_config_is_valid(config: Config):
    for item in [
        "permeability",
    ]:
        ensure_parameter_isset(config, item)
