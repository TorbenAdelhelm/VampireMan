# Vary My Params

This tool allows a user to describe how parameters for a data set should be varied.
After describing which parameters should be varied in which manner, i.e. permeability should be a constant field, with values varying between 1 and 10, the program proceeds actually varying these parameters and also renders all files necessary to run the simulations afterwards.
Then, the tool starts a simulation based on the rendered input files and finally visualizes the results.

Currently, only the preparation for the simulation software `pflotran` workflow is implemented.

The minimum required python version is 3.11.

## Quickstart

After installing the dependencies, you can run the most basic default case by executing `python -m vary_my_params`.
This command interactively guides you through the preparation stages of the pipeline and renders all files needed to execute a pflotran simulation to the directory specified by `output_directory` in the configs `general` section (which is by default the date in UTC ISO 8601 format `./datasets_out/2024-08-17T10:06:15+00:00`).

When the program has exited successfully, `cd datasets_out/<name of the output directory>` into the directory and look at the results.

## Installation of the Software

Currently, there are three supported ways of installing and running the software.
Depending on your environment, choose one of the following.

### Ubuntu

1. Install at least python 3.11 (e.g., `apt install python3`)
1. Install poetry (e.g., `pip install poetry`)
1. Clone this repository and `cd` into it
1. Install the dependencies from the project root (i.e., `poetry install`)
1. Enter a poetry shell (e.g., `poetry shell`)
1. [Install pflotan 5.0.0](https://www.pflotran.org/documentation/user_guide/how_to/installation/installation.html)

### Installing Nix on Uni Stuttgart IPVS Servers

1. Clone the repository
1. Run `bash setup.sh` in the project root
1. Log out and in again to apply the changes to the `PATH` environment variable
1. Enter `nix develop` to load the Nix environment

### Nix

1. If you have [Nix](https://nixos.org) and [direnv](https://direnv.net/) installed, simply enter the project root and type in `direnv allow`. Wait for a shell and you are done!

## Stages

The program sequentially runs several stages passing the outputs of the previous stage onto the next one.

Namely, the stages are (in this order):
- load_config
    load the user provided values and parameters etc
- prepare_parameters
    generate heatpumps from the heatpumps parameters
- vary_parameters
    varies the values loaded from the config step
- prepare_simulation
- run_simulation
- collect_results
- visualize_results
