import logging

import matplotlib.pyplot as plt
import numpy as np
from h5py import File


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


def plot_vary_field(cells, filename, parameter_name):
    fig, axes = plt.subplots(2, 2, figsize=(10, 6))
    fig.suptitle(f"{parameter_name.title()} perlin field")
    axes = axes.ravel()
    axes[0].imshow(cells[:, :, 0])
    axes[2].imshow(cells[:, 0, :])
    axes[3].imshow(cells[0, :, :])
    axes[0].set_title("yz")
    axes[2].set_title("xz")
    axes[3].set_title("xy")
    for i in range(0, 4):
        axes[i].axis("off")
    fig.tight_layout()
    fig.savefig(f"{filename}.png")
    plt.close(fig)
