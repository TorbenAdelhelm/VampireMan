import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from h5py import File

from ...config import Data


def save_vary_field(filename, number_cells, cells, parameter_name: str = "permeability"):
    n = number_cells[0] * number_cells[1] * number_cells[2]
    # create integer array for cell ids
    iarray = np.arange(n, dtype="i4")
    iarray[:] += 1  # convert to 1-based
    cells_array_flatten = cells.reshape(n, order="F")

    with File(filename, mode="w") as h5file:
        h5file.create_dataset("Cell Ids", data=iarray)
        h5file.create_dataset(parameter_name.title(), data=cells_array_flatten)

    logging.info(f"Created a {parameter_name}-field")


def plot_vary_field(datapoint_dir: Path, parameter: Data):
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    fig.suptitle(f"{parameter.name.title()} perlin field")
    axes = axes.ravel()
    if not isinstance(parameter.value, np.ndarray):
        raise ValueError("Cannot visualize something that is not an np.ndarray")
    axes[0].imshow(parameter.value[:, :, 0])
    axes[2].imshow(parameter.value[:, 0, :])
    axes[3].imshow(parameter.value[0, :, :])
    axes[0].set_title("yz")
    axes[2].set_title("xz")
    axes[3].set_title("xy")
    for i in range(0, 4):
        axes[i].axis("off")
    fig.tight_layout()
    fig.savefig(datapoint_dir / f"{parameter.name}_field.png")
    plt.close(fig)
