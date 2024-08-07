from ..config import Config


def vary_params(config: Config) -> Config:
    for index in range(config.general.number_datapoints):
        data = {
            "permeability": config.parameters.get("permeability").value,
            "number_cells": config.parameters.get("number_cells").value,
            "cell_resolution": config.parameters.get("cell_resolution").value,
            "time": {"final_time": 27.5},
            "temperature": config.parameters.get("temperature").value + index,
        }
        config.datapoints.append(data)

    return config
