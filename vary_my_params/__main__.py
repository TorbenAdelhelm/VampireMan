import logging

from . import cli

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s: %(filename)s:%(lineno)s in %(funcName)s() > %(message)s"
)

if __name__ == "__main__":
    cli.main()
