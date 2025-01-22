# This file marks that vampireman is a python module
import pathlib

# These are simple re-export for easier access
from .loading_stage import loading_stage as loading_stage
from .preparation_stage import preparation_stage as preparation_stage
from .render_stage import render_stage as render_stage
from .simulation_stage import simulation_stage as simulation_stage
from .validation_stage import validation_stage as validation_stage
from .variation_stage import variation_stage as variation_stage
from .visualization_stage import visualization_stage as visualization_stage

# Uses the README.md in the project root as documentation
try:
    with open(pathlib.Path(__file__).parent.parent.resolve() / "README.md", encoding="utf8") as readme:
        __doc__ = "".join(readme.readlines())
except Exception:
    __doc__ = "Vary parameters in a structured, declarative, reproducible way."
