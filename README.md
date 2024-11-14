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

## Settings

There are several example settings in [the settings directory](./settings).
Those settings represent test cases and are also semantically validated when running pytest.

All grids are unstructured and have three dimensions with a cell resolution of 5 meters in each dimension.
Two dimensional grids are implicitly converted to three dimensions by adding a `z` coordinate with the value of 1.

Further, all cases have the similarities:
- random seed is always set to `0`
- output directory is set to `./datasets_out/<casename>`.
- workflow is `pflotran`
- profiling is disabled
- simulation time is 27.5 years
- interactive is set to false

| case                                           | grid         | datapoint(s) | heat pump(s)   | permeability | hydraulic head | temperature | description                                                                               |
|------------------------------------------------|--------------|--------------|----------------|--------------|----------------|-------------|-------------------------------------------------------------------------------------------|
| [0](./settings/case0_default.yaml)             | (32,128,1) | 1            | 1 fix          | fix          | fix            | fix         | Takes over all default values from the program.                                           |
| [1](./settings/case1_vary-pressure-const.yaml) | (32,128,1) | 2            | 1 fix          | const        | const          | fix         | Demonstrates CONST vary method.                                                           |
| [2](./settings/case2_vary-hp-positions.yaml)   | (64,256,1) | 2            | 1 fix, 2 space | fix          | fix            | fix         | Demonstrates the SPACE vary method for heat pumps.                                        |
| [3](./settings/case3_allin1.yaml)              | (32,128,1) | 3            | 2 space        | space        | fix            | fix         | Demonstrates the SPACE vary method for heat pumps and hydrogeological parameters.         |
| [4](./settings/case4_extend-plumes.yaml)       | (16,128,1) | 3            | 1 fix          | space        | const          | fix         | Longer domain and long heat plumes while having the permeability varied spatially.        |
| [5](./settings/case5_3d.yaml)                  | (16,64,16) | 1            | 1 fix          | fix          | fix            | fix         | case0 in a 3D domain with z > 1                                                           |
| [6](./settings/case6_vertical_aniso.yaml)      | (16,64,16) | 1            | 1 fix          | fix          | fix            | fix         | case5 with a vertical anisotropy ratio of 10.                                             |
| [9](./settings/case9_seasonal-changes.yaml)    | (32,128,1) | 1            | 2 fix          | fix          | fix            | fix         | Demonstrates time based changes in the heat pump injection values (temperature and rate).
