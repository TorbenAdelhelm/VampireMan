from ..config import Config, DataType, Parameter, Vary


def get_defaults() -> Config:
    config = Config()

    config.parameters["number_cells"] = Parameter(
        name="number_cells",
        data_type=DataType.ARRAY,
        value=[64, 256, 1],
    )
    config.parameters["cell_resolution"] = Parameter(
        name="cell_resolution",
        data_type=DataType.ARRAY,
        value=[5, 5, 5],
    )
    config.parameters["permeability"] = Parameter(
        name="permeability",
        data_type=DataType.PERLIN,
        value={
            "factor": 40,
            "frequency": [1.8, 1.8, 1.8],
            "max": 1.2882090745857623e-1,
            "min": 1.2882090745857623e-10,
        },
        vary=Vary.SPACE,
    )
    config.parameters["temperature"] = Parameter(
        name="temperature",
        data_type=DataType.SCALAR,
        value=10.6,
    )

    return config


def ensure_value(config, name):
    value = config.parameters.get(name)
    if value is None:
        raise ValueError(f"`{name}` must not be None")


def ensure_config_is_valid(config: Config):
    for item in [
        "permeability",
        "cell_resolution",
        "number_cells",
    ]:
        ensure_value(config, item)
