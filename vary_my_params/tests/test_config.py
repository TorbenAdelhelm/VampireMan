import pytest

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
    config.override_with(Config.from_dict(dict_config_valid))
    assert config.general.interactive is False

    # Check if additional keys get detected
    with pytest.raises(ValueError):
        Config.from_dict({"additional": "key"})

    with pytest.raises(ValueError):
        Config().general.from_dict({"additional": "key"})

    # Check if wrong values get caught
    with pytest.raises(ValueError):
        config = Config.from_dict({"steps": 5})

    with pytest.raises(ValueError):
        config = Config.from_dict({"steps": ["test", {}]})

    with pytest.raises(ValueError):
        config = Config.from_dict({"steps": []})
    config = Config.from_dict({"steps": ["one", "two"]})
    assert len(config.steps) == 2

    with pytest.raises(ValueError):
        config = Config.from_dict(dict_config_invalid)

    # Check if reading yaml files works correctly
    config = Config.from_yaml("vary_my_params/tests/test_config_valid.yaml")

    with pytest.raises(ValueError):
        config = Config.from_yaml("vary_my_params/tests/test_config_invalid.yaml")

    with pytest.raises(OSError):
        config = Config.from_yaml("/nonexistent/test.yaml")
