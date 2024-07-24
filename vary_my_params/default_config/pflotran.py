from ..config import Config


def get_defaults():
    return Config(
        general={
            "workflow": "pflotran",
        },
        parameters={
            "number_cells": {
                "data_type": "array",
                "vary": None,
                "input_source": "manual",
                "value": [64, 256, 1],
            },
            "cell_resolution": {
                "data_type": "array",
                "vary": None,
                "input_source": "manual",
                "value": [5, 5, 5],
            },
            "permeability": {
                "data_type": "scalar",
                "vary": None,
                "input_source": "manual",
                "value": 1.3576885245230967e-09,
            },
        },
    )
