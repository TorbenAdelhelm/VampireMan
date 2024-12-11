from pathlib import Path

import pytest
from pydantic import ValidationError

from vary_my_params.data_structures import State


def test_state_override():
    # Check if the basics of the State work
    state = State()
    assert state.general.interactive is True

    # Check if overrides work
    state.override_with(
        State(
            **{
                "general": {
                    "interactive": False,
                    "random_seed": 1234,
                }
            }
        )
    )
    assert state.general.interactive is False


def test_state_dont_allow_extras():
    # Check if additional keys get detected
    with pytest.raises(ValidationError):
        State(**{"additional": "key"})


def test_state_catch_wrong_values():
    # Check if wrong values get caught
    with pytest.raises(ValidationError):
        State(**{"pure": 5})

    with pytest.raises(ValidationError):
        print(State(**{"general": {"number_cells": ["test", {}]}}))


def test_state_invalid_state():
    with pytest.raises(ValidationError):
        State(
            **{
                "general": {
                    "workflow": "new-thing",
                }
            }
        )


def test_state_read_correct_yaml():
    # Check if reading yaml files works correctly
    State.from_yaml("vary_my_params/tests/test_settings_valid.yaml")


def test_state_default_cases():
    pathlist = Path("./settings/").glob("*.yaml")
    # raise ValueError(os.getcwd())
    for setting in pathlist:
        try:
            State.from_yaml(setting)
        except ValidationError as err:
            raise ValueError(f"{err}\n\n{setting} not correct") from err


def test_state_read_incorrect_yaml():
    with pytest.raises(ValueError):
        State.from_yaml("vary_my_params/tests/test_settings_invalid.yaml")


def test_state_read_nonexistent_yaml():
    with pytest.raises(OSError):
        State.from_yaml("/nonexistent/test.yaml")


def test_state_rng():
    state = State()

    # These value should always be the same, due to the fixed seed
    assert state.get_rng().random() == 0.6369616873214543
    assert state.get_rng().random(3).tolist() == [0.2697867137638703, 0.04097352393619469, 0.016527635528529094]


def test_3d_param():
    state = State(**{"general": {"number_cells": [3, 2]}})
    assert state.general.number_cells[0] == 3
    assert state.general.number_cells[1] == 2
    assert state.general.number_cells[2] == 1

    with pytest.raises(ValidationError):
        state = State(**{"general": {"number_cells": [3]}})
    with pytest.raises(ValidationError):
        state = State(**{"general": {"number_cells": [1, 2, 3, 4]}})
