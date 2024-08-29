import pytest
from pydantic import ValidationError

from vary_my_params.config import Config


def test_config():
    dict_config_valid = {
        "general": {
            "interactive": False,
            "random_seed": 1234,
        }
    }

    dict_config_invalid = {
        "general": {
            "workflow": "new-thing",
        }
    }

    # Check if the basics of the config work
    config = Config()
    assert config.general.interactive is True

    # Check if overrides work
    config.override_with(Config(**dict_config_valid))
    assert config.general.interactive is False

    # Check if additional keys get detected
    with pytest.raises(ValidationError):
        Config(**{"additional": "key"})

    # Check if wrong values get caught
    with pytest.raises(ValidationError):
        config = Config(**{"steps": 5})

    with pytest.raises(ValidationError):
        config = Config(**{"steps": ["test", {}]})

    with pytest.raises(ValidationError):
        config = Config(**{"steps": []})
    config = Config(**{"steps": ["one", "two"]})
    assert len(config.steps) == 2

    with pytest.raises(ValidationError):
        config = Config(**dict_config_invalid)

    # Check if reading yaml files works correctly
    config = Config.from_yaml("vary_my_params/tests/test_config_valid.yaml")

    with pytest.raises(ValueError):
        config = Config.from_yaml("vary_my_params/tests/test_config_invalid.yaml")

    with pytest.raises(OSError):
        config = Config.from_yaml("/nonexistent/test.yaml")
