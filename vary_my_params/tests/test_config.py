from pathlib import Path

import pytest
from pydantic import ValidationError

from vary_my_params.config import Config


def test_config_override():
    # Check if the basics of the config work
    config = Config()
    assert config.general.interactive is True

    # Check if overrides work
    config.override_with(
        Config(
            **{
                "general": {
                    "interactive": False,
                    "random_seed": 1234,
                }
            }
        )
    )
    assert config.general.interactive is False


def test_config_dont_allow_extras():
    # Check if additional keys get detected
    with pytest.raises(ValidationError):
        Config(**{"additional": "key"})


def test_config_catch_wrong_values():
    # Check if wrong values get caught
    with pytest.raises(ValidationError):
        config = Config(**{"steps": 5})

    with pytest.raises(ValidationError):
        config = Config(**{"steps": ["test", {}]})

    with pytest.raises(ValidationError):
        config = Config(**{"steps": []})
    config = Config(**{"steps": ["one", "two"]})
    assert len(config.steps) == 2


def test_config_invalid_config():
    with pytest.raises(ValidationError):
        Config(
            **{
                "general": {
                    "workflow": "new-thing",
                }
            }
        )


def test_config_read_correct_yaml():
    # Check if reading yaml files works correctly
    Config.from_yaml("vary_my_params/tests/test_config_valid.yaml")


def test_config_default_cases():
    pathlist = Path("./settings/").glob("*.yaml")
    # raise ValueError(os.getcwd())
    for setting in pathlist:
        try:
            Config.from_yaml(setting)
        except ValidationError as err:
            raise ValueError(f"{err}\n\n{setting} not correct") from err


def test_config_read_incorrect_yaml():
    with pytest.raises(ValueError):
        Config.from_yaml("vary_my_params/tests/test_config_invalid.yaml")


def test_config_read_nonexistent_yaml():
    with pytest.raises(OSError):
        Config.from_yaml("/nonexistent/test.yaml")


def test_config_rng():
    config = Config()

    # These value should always be the same, due to the fixed seed
    assert config.get_rng().random() == 0.6369616873214543
    assert config.get_rng().random(3).tolist() == [0.2697867137638703, 0.04097352393619469, 0.016527635528529094]
