import numpy as np

from .config import Config


def random_float(config: Config):
    return np.random.default_rng(seed=config.general.random_seed).random()


def random_nd_array(config: Config, size: int):
    return np.random.default_rng(seed=config.general.random_seed).random(size)
