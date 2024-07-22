from ..config import Config


def get_defaults():
    return Config(
        general={
            "workflow": "pflotran",
        },
        parameters={
            "grid": {
                "data_type": "array",
                "vary": None,
                "input_source": "manual",
                "value": [64, 256, 1],
            },
            "permeability": {
                "data_type": "scalar",
                "vary": None,
                "input_source": "manual",
                "value": 1.3576885245230967e-09,
            },
        },
    )
