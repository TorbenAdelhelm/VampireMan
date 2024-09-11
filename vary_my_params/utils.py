import logging
import sys

from .config import Config


def get_answer(config: Config, question: str, exit_if_no: bool = False) -> bool:
    """Ask a yes/no question on the command line and return True if the answer is yes and False if the answer is no"""
    if not config.general.interactive:
        return True
    try:
        match input(f"{question} Y/n "):
            case "n" | "N" | "no" | "q":
                if exit_if_no:
                    logging.info("Exiting as instructed")
                    sys.exit(0)
                return False
            case _:
                return True
    except KeyboardInterrupt:
        logging.info("Exiting as instructed")
        sys.exit(0)
