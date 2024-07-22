from ..config import Config


def vary_params(config: Config) -> Config:
    config.data = config.parameters
    return config
