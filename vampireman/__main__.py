import logging
import warnings

# This supresses unwanted output as the library tries to write to its installation directory. Only required once.
with warnings.catch_warnings(action="ignore"):
    import numpydantic as numpydantic

from . import cli

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s: %(filename)s:%(lineno)s in %(funcName)s() > %(message)s"
)

if __name__ == "__main__":
    cli.main()
