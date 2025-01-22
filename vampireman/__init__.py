# This file marks that vampireman is a python module
import pathlib

# Uses the README.md in the project root as documentation
try:
    with open(pathlib.Path(__file__).parent.parent.resolve() / "README.md", encoding="utf8") as readme:
        __doc__ = "".join(readme.readlines())
except Exception:
    __doc__ = "Vary parameters in a structured, declarative, reproducible way."
