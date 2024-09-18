import logging
from argparse import Namespace

from .config import Config, load_config
from .utils import get_answer, get_workflow_module, profile_stage


@profile_stage
def ensure_config_is_valid(config: Config) -> Config:
    return get_workflow_module(config.general.workflow).ensure_config_is_valid(config)


@profile_stage
def run_vary_params(config: Config) -> Config:
    get_answer(config, "Do you want to run the stage parameter variation?", True)
    config = get_workflow_module(config.general.workflow).vary_params(config)
    print("Following datapoints will be used")
    for datapoint in config.datapoints:
        print(datapoint)
    return config


@profile_stage
def run_render(config: Config):
    get_answer(config, "Do you want to run the stage prepare_simulation?", True)
    get_workflow_module(config.general.workflow).render(config)


@profile_stage
def run_simulation(config: Config):
    get_answer(config, "Do you want to run the stage run_simulation?", True)
    get_workflow_module(config.general.workflow).run_simulation(config)


@profile_stage
def run_visualization(config: Config):
    get_answer(config, "Do you want to run the stage run_visualization?", True)
    get_workflow_module(config.general.workflow).plot_simulation(config)


def run(args: Namespace):
    workflow_module = get_workflow_module(args.workflow)

    config = load_config(args, workflow_module)
    config = ensure_config_is_valid(config)

    print(config)
    logging.debug("Will run all stages")

    config = run_vary_params(config)

    run_render(config)
    run_simulation(config)
    # XXX: visualize in between the steps
    run_visualization(config)
