import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any

import h5py
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

from vary_my_params.prepare_simulation.pflotran.pflotran_write_permeability import plot_vary_field

from ..config import Config, HeatPump

TimeData = OrderedDict[str, dict[str, Any]]


def pflotran_time_to_year(time_step: str) -> float:
    # Get year from '   3 Time  5.00000E+00 y'
    return float(time_step.split(" ")[-2])


# This doesn't work
# def asdf(data: TimeData, path: Path):
#     time_steps = len(data)
#     key, val = data.popitem()
#     cols = len(val)
#     data[key] = val
#
#     _, axes = plt.subplots(time_steps, cols, figsize=(20 * cols, 5 * time_steps))
#
#     for index, (time_step, time_data) in enumerate(data.items()):
#         temp_data = time_data.get("Temperature [C]")
#         for level in range(len(temp_data[2])):
#             plt.subplot()
#             set_trace()
#
#             # Make the 3D data 2D so it can be plotted
#             plot_data = temp_data[:, :, level]
#             plt.imshow(plot_data)
#
#             plt.xlabel("cells y")
#             plt.ylabel("cells x or z")
#             aligned_colorbar(label=f"Temp in C at z = {level}")
#
#         pic_file_name = path / "Pflotran_properties_2d-{row}.jpg"
#         logging.info(f"Resulting picture is at {pic_file_name}")
#         plt.savefig(pic_file_name)


def plot_simulation(config: Config):
    for datapoint in config.datapoints:
        datapoint_path = config.general.output_directory / f"datapoint-{datapoint.index}"

        with h5py.File(datapoint_path / "pflotran.h5") as file:
            list_to_plot = make_plottable(config, file)

        plot_y(list_to_plot, datapoint_path)
        plot_isolines(config, list_to_plot, datapoint_path)
        # TODO: make this more general
        plot_vary_field(datapoint_path, datapoint.data["permeability"])

        # print_heatpump_temp(config, list_to_plot)


def print_heatpump_temp(config: Config, data: TimeData):
    # XXX is this needed?
    key, value = data.popitem()
    data[key] = value
    temp_data = value["Temperature [C]"]
    years = pflotran_time_to_year(key)

    for index, datapoint in enumerate(config.datapoints):
        heatpumps = [{name: d.value} for name, d in datapoint.data.items() if isinstance(d.value, HeatPump)]
        for name, heatpump in heatpumps:
            assert isinstance(heatpump, HeatPump)
            location = heatpump.location
            try:
                temp = np.round(temp_data[location[0], location[1]], 4)
                logging.info("datapoint %s: Temperature at HP at '%s' (%s years): %s C", index, name, years, temp)
            except Exception as err:
                logging.error("Could not get HP temp: %s", err)


def make_plottable(config: Config, hdf5_file: h5py.File) -> TimeData:
    dimensions = config.general.number_cells

    datapoints_to_plot: TimeData = OrderedDict()

    for time_step, timegroup in hdf5_file.items():
        datapoints_to_plot[time_step] = OrderedDict()

        # XXX: why not render the first timestep?
        for property, property_values in timegroup.items():
            # Read from the hdf5 file
            data = np.array(property_values)

            # Reshape the data to match the 3D space of the domain
            data = data.reshape(dimensions, order="F")

            datapoints_to_plot[time_step][property] = data
    return datapoints_to_plot


def plot_y(data: TimeData, path: Path):
    rows = len(data)
    key, val = data.popitem()
    cols = len(val)
    data[key] = val

    _, axes = plt.subplots(rows, cols, figsize=(20 * cols, 5 * rows))

    for row, (_, time_data) in enumerate(data.items()):
        for col, (property_name, property_data) in enumerate(time_data.items()):
            plt.sca(axes[row][col])

            # Make the 3D data 2D so it can be plotted
            level = int((property_data.shape[2] - 1) / 2)
            plot_data = property_data[:, :, level]
            plt.imshow(plot_data)

            plt.xlabel("cells y")
            plt.ylabel("cells x or z")
            aligned_colorbar(label=property_name)

    pic_file_name = path / "Pflotran_properties_2d.jpg"
    logging.info(f"Resulting picture is at {pic_file_name}")
    plt.savefig(pic_file_name)


def plot_isolines(config: Config, data: TimeData, path: Path):
    rows = len(data)
    _, axes = plt.subplots(rows, 1, figsize=(20, 5 * rows))

    # XXX: What should be the default values?
    level_min = float("inf")
    level_max = -float("inf")
    level_step = None

    for _, time_data in data.items():
        level_min = min(level_min, time_data["Temperature [C]"].min())
        level_max = max(level_max, time_data["Temperature [C]"].max())
    if level_min > level_max:
        raise ValueError("level_min is larger than level_max")
    # XXX: Why 24 here?
    level_step = (level_max - level_min) / 24

    levels = np.arange(level_min, level_max, level_step)

    for index, (time_step, time_data) in enumerate(data.items()):
        property_data = time_data.get("Temperature [C]")
        assert property_data is not None

        plt.sca(axes[index])

        x_ticks = ticker.FuncFormatter(lambda x, pos: f"{x*config.general.cell_resolution[0]:g}")
        y_ticks = ticker.FuncFormatter(lambda y, pos: f"{y*config.general.cell_resolution[1]:g}")
        axes[index].xaxis.set_major_formatter(x_ticks)
        axes[index].yaxis.set_major_formatter(y_ticks)

        # Make the 3D data 2D so it can be plotted
        level = int((property_data.shape[2] - 1) / 2)
        plot_data = property_data[:, :, level]
        plt.imshow(plot_data)

        plt.contourf(plot_data, levels=levels, cmap="RdBu_r")

        plt.title(f"{pflotran_time_to_year(time_step)} years")
        # XXX this is not meters, it is cells. Should be number_cells * cell_resolution
        plt.xlabel("y [m]")
        plt.ylabel("x [m]")
        aligned_colorbar(label="Temperature [°C]")

    pic_file_name = path / "Pflotran_isolines.jpg"
    logging.info(f"Resulting picture is at {pic_file_name}")
    plt.suptitle("Isolines of Temperature [°C]")
    plt.savefig(pic_file_name)


def aligned_colorbar(*args, **kwargs):
    cax = make_axes_locatable(plt.gca()).append_axes("right", size=0.3, pad=0.05)
    plt.colorbar(*args, cax=cax, **kwargs)
