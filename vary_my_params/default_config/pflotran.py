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
        },
    )
