import logging
from argparse import Namespace

from .config import Config, ensure_config_is_valid, load_config
from .utils import (
    create_dataset_and_datapoint_dirs,
    get_answer,
    get_workflow_module,
    profile_function,
    read_in_files,
    write_data_to_verified_json_file,
)
from .vary_params.vary import calculate_hp_coordinates, generate_heatpumps, handle_time_based_params, vary_params


@profile_function
def prepare_parameters(config: Config) -> Config:
    config = read_in_files(config)
    config = generate_heatpumps(config)
    config = calculate_hp_coordinates(config)
    config = handle_time_based_params(config)
    return config


@profile_function
def run_vary_params(config: Config) -> Config:
    get_answer(config, "Do you want to run the stage parameter variation?", True)
    config = vary_params(config)
    print("Following datapoints will be used")
    for datapoint in config.datapoints:
        print(datapoint)
        write_data_to_verified_json_file(
            config, config.general.output_directory / f"datapoint-{datapoint.index}" / "datapoint.json", datapoint
        )
    return config


@profile_function
def run_render(config: Config):
    get_answer(config, "Do you want to run the stage prepare_simulation?", True)
    get_workflow_module(config.general.workflow).render(config)


@profile_function
def run_simulation(config: Config):
    get_answer(config, "Do you want to run the stage run_simulation?", True)
    get_workflow_module(config.general.workflow).run_simulation(config)


@profile_function
def run_visualization(config: Config):
    get_answer(config, "Do you want to run the stage run_visualization?", True)
    get_workflow_module(config.general.workflow).plot_simulation(config)


def run(args: Namespace):
    config = load_config(args)
    config = prepare_parameters(config)
    config = ensure_config_is_valid(config)

    create_dataset_and_datapoint_dirs(config)
    write_data_to_verified_json_file(config, config.general.output_directory / "config.json", config)

    # Where do we check this?
    logging.debug("Will run all stages")

    print("This is the config that is going to be used:")
    print(config)

    config = run_vary_params(config)

    run_render(config)
    run_simulation(config)
    run_visualization(config)
