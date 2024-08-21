import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any

import h5py
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import make_axes_locatable

from ..config import Config, DataType

TimeData = OrderedDict[str, dict[str, Any]]


def pflotran_time_to_year(time_step: str) -> float:
    # Get year from '   3 Time  5.00000E+00 y'
    return float(time_step.split(" ")[-2])


def plot_sim(config: Config):
    for datapoint in config.datapoints:
        datapoint_path = config.general.output_directory / f"datapoint-{datapoint.index}"

        with h5py.File(datapoint_path / "pflotran.h5") as file:
            list_to_plot = make_plottable_and_2D(config, file)

        plot_y(list_to_plot, datapoint_path)
        plot_isolines(config, list_to_plot, datapoint_path)

        # print_heatpump_temp(config, list_to_plot)


def print_heatpump_temp(config: Config, data: TimeData):
    # XXX is this needed?
    key, value = data.popitem()
    data[key] = value
    temp_data = value["Temperature [C]"]
    years = pflotran_time_to_year(key)

    for index, datapoint in enumerate(config.datapoints):
        heatpumps = [{name: d.to_value()} for name, d in datapoint.data.items() if d.data_type == DataType.HEATPUMP]
        for heatpump in heatpumps:
            for hp_name, hp_val in heatpump.items():
                location = hp_val["location"]
                try:
                    temp = np.round(temp_data[location[0], location[1]], 4)
                except Exception as err:
                    logging.error("Could not get HP temp: %s", err)
                logging.info(f"datapoint %s: Temperature at HP at '%s' (%s years): %s C", index, hp_name, years, temp)


def make_plottable_and_2D(config: Config, hdf5_file: h5py.File) -> TimeData:
    dimensions = config.general.number_cells.value

    datapoints_to_plot: TimeData = OrderedDict()

    for time_step, timegroup in hdf5_file.items():
        datapoints_to_plot[time_step] = OrderedDict()

        # XXX: why not render the first timestep?
        for property, property_values in timegroup.items():
            # Read from the hdf5 file
            data = np.array(property_values)

            # Reshape the data to match the 3D space of the domain
            data = data.reshape(dimensions, order="F")

            # Make the 3D data 2D so it can be plotted
            data = data[:, :, 0]

            datapoints_to_plot[time_step][property] = data
    return datapoints_to_plot


def plot_y(data: TimeData, path: Path):
    rows = len(data)
    key, val = data.popitem()
    cols = len(val)
    data[key] = val

    _, axes = plt.subplots(rows, cols, figsize=(20 * cols, 5 * rows))

    for row, (_, time_data) in enumerate(data.items()):
        for col, (property, property_data) in enumerate(time_data.items()):
            plt.sca(axes[row][col])
            plt.imshow(property_data)
            # XXX why this?
            plt.gca().invert_yaxis()
            plt.xlabel("cells y")
            plt.ylabel("cells x or z")
            aligned_colorbar(label=property)

    pic_file_name = path / "Pflotran_properties.jpg"
    logging.info(f"Resulting picture is at {pic_file_name}")
    plt.savefig(pic_file_name)


def plot_isolines(config: Config, data: TimeData, path: Path):
    rows = len(data)
    _, axes = plt.subplots(rows, 1, figsize=(20, 5 * rows))
    # TODO read min/max from the data
    levels = np.arange(10.6, 15.6, 0.25)

    # XXX why do we skip timestep 0 again?
    for index, (time_step, time_data) in enumerate(data.items()):
        temp = time_data.get("Temperature [C]")

        plt.sca(axes[index])
        plt.contourf(temp, levels=levels, cmap="RdBu_r")
        # XXX why?
        plt.gca().invert_yaxis()

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
