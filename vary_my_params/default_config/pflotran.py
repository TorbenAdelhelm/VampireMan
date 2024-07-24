from ..config import Config, DataType, Parameter


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
        data_type=DataType.SCALAR,
        value=1.3576885245230967e-09,
    )

    return config
