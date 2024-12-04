import logging

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
