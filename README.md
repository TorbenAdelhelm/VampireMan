# Vary My Params

This tool allows a user to describe how parameters for a simulation should be varied.
After describing which parameters should be varied in which manner, the program proceeds actually varying these parameters and also renders all files necessary to run the simulation afterwards.

Currently, only the `pflotran` workflow is implemented.

The minimum required python version is 3.10.

## Quickstart

After installing the dependencies, you can run the most basic default case by executing `python -m vary_my_params`.
This command will interactively guide you through the stages of the pipeline and render all files needed to execute a pflotran simulation to the directory specified by `output_directory` in the configs `general` section (which is by default `./out_dir`).

When the program has exited successfully, `cd out_dir` into the directory and run pflotran (since this is the default case) by either executing `pflotran` or `mpirun -n <processor_cores> pflotran`.

## Installation

### Ubuntu

1. Install at least python 3.10 (e.g., `apt install python3`)
1. Install poetry (e.g., `pip install poetry`)
1. Enter a poetry shell (e.g., `poetry shell`)
1. Install pflotan 5.0.0

### Nix

1. If you have [Nix](https://nixos.org) and [direnv](https://direnv.net/) installed, simply enter the project root and type in `direnv allow`. Wait for a shell and you are done!

## Stages

The program runs several stages, one after another, passing the outputs of the previous stage onto the next one.

Namely, the stages are (in this order):
- load_config
    load the user provided values and parameters etc
- vary_parameters
    varies the values loaded from the config step
- prepare_simulation
- run_simulation
- collect_results
- visualize_results
