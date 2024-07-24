from ..config import Config


def vary_params(config: Config) -> Config:
    config.data["permeability"] = config.parameters.get("permeability").value
    config.data["number_cells"] = config.parameters.get("number_cells").value
    config.data["cell_resolution"] = config.parameters.get("cell_resolution").value
    config.data["time"] = {"final_time": 27.5}

    return config
