from typing import Any, cast

import noise
import numpy as np
from numpy.typing import NDArray

from ..data_structures import Distribution, Parameter, State, ValueMinMax, ValuePerlin


def make_perlin_grid(
    aimed_min: float,
    aimed_max: float,
    state: State,
    offset: NDArray[np.floating[Any]],
    freq: list[float],
) -> NDArray[np.floating[Any]]:
    grid_dimensions: list[int] = state.general.number_cells.tolist()  # pyright: ignore

    # adapted by Manuel Hirche

    # We sample the permeability from 3 dimensional perlin noise that extends indefinetly.
    # To introduce randomness the starting point of our sampling is drawn from a uniform
    # distribution. From there we are moving a multiple of our simulation area for every
    # sample to get non-overlapping fields. The simulation area is scaled to a unit cube so
    # conveniently we can move by 1 in x directon (in this direction the scaled area
    # will be << 1)

    # Scale the simulation area down into a unit cube
    simulation_area_max = max(grid_dimensions)
    scale = np.array(grid_dimensions) / simulation_area_max

    # Create the grid indices
    i, j, k = np.meshgrid(
        np.arange(grid_dimensions[0]), np.arange(grid_dimensions[1]), np.arange(grid_dimensions[2]), indexing="ij"
    )

    # Normalize
    x = (i / grid_dimensions[0] * scale[0] + offset[0]) * freq[0]
    y = (j / grid_dimensions[1] * scale[1] + offset[1]) * freq[1]
    z = (k / grid_dimensions[2] * scale[2] + offset[2]) * freq[2]

    values = np.vectorize(noise.pnoise3)(x, y, z)

    # scale to intended range
    current_min = np.min(values)
    current_max = np.max(values)

    values = (values - current_min) / (current_max - current_min)
    values = values * (aimed_max - aimed_min) + aimed_min

    return values


def create_perlin_field(state: State, parameter: Parameter):
    base_offset = state.get_rng().random(3) * 4242

    if not isinstance(parameter.value, ValuePerlin):
        raise ValueError()

    freq_factor = parameter.value.frequency

    if isinstance(freq_factor, ValueMinMax):
        # If the frequency is `ValueMinMax`, get random values for x,y,z
        rand = state.get_rng()

        min = freq_factor.min
        max = freq_factor.max

        val1 = max - (rand.random() * (max - min))
        val2 = max - (rand.random() * (max - min))
        val3 = max - (rand.random() * (max - min))

        freq_factor = [val1, val2, val3]

    if not isinstance(freq_factor, list):
        raise ValueError()

    vary_min = parameter.value.min
    vary_max = parameter.value.max

    if parameter.distribution == Distribution.LOG:
        vary_min = np.log10(vary_min)
        vary_max = np.log10(vary_max)

    cells = make_perlin_grid(
        vary_min,
        vary_max,
        state,
        base_offset,
        freq_factor,
    )

    if parameter.distribution == Distribution.LOG:
        cells = 10**cells

    if parameter.name == "pressure_gradient":
        cells = calc_pressure_from_gradient_field(cells, state, parameter)

    return cells


def create_const_field(state: State, value: float | NDArray):
    if np.size(value) > 1:
        value = value.reshape(state.general.number_cells)  # pyright: ignore
    return np.full(cast(np.ndarray, state.general.number_cells), value)


def calc_pressure_from_gradient_field(
    gradient_field: NDArray[np.floating[Any]], state: State, parameter: Parameter
) -> NDArray[np.floating[Any]]:
    # XXX: is this function correctly implemented?

    value = parameter.value
    assert isinstance(value, ValueMinMax)

    # scale pressure field to min and max values from state
    current_min = np.min(gradient_field)
    current_max = np.max(gradient_field)

    new_min = value.min
    new_max = value.max

    gradient_field = (gradient_field - current_min) / (current_max - current_min) * (new_max - new_min) + new_min

    reference = 101325  # Standard atmosphere pressure in Pa
    resolution = state.general.cell_resolution

    pressure_field = np.zeros_like(gradient_field)
    pressure_field[:, 0] = reference
    for i in range(1, pressure_field.shape[1]):
        pressure_field[:, i] = pressure_field[:, i - 1] + gradient_field[:, i] * resolution * 1000
    pressure_field = pressure_field[::-1]

    return pressure_field
