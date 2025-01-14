import logging
from pathlib import Path
from typing import cast

import numpy as np

from ...data_structures import State


def write_mesh_and_border_files(state: State, output_dir: Path) -> None:
    write_lines_to_file("mesh.uge", render_mesh(state), output_dir)

    north, east, south, west = render_borders(state)
    write_lines_to_file("north.ex", north, output_dir)
    write_lines_to_file("east.ex", east, output_dir)
    write_lines_to_file("south.ex", south, output_dir)
    write_lines_to_file("west.ex", west, output_dir)

    logging.debug("Rendered {north,east,south,west}.ex")


def write_lines_to_file(file_name: str, output_strings: list[str], output_dir: Path):
    with open(f"{output_dir}/{file_name}", "w", encoding="utf8") as file:
        file.writelines(output_strings)


def render_mesh(state: State) -> list[str]:
    xGrid, yGrid, zGrid = cast(np.ndarray, state.general.number_cells)
    resolution = state.general.cell_resolution

    volume = resolution**3
    face_area = resolution**2

    # CELLS <number of cells>
    # <cell id> <x> <y> <z> <volume>
    # ...
    # CONNECTIONS <number of connections>
    # <cell id a> <cell id b> <face center coordinate x> <face y> <face z> <area of the face>

    output_string_cells = ["CELLS " + str(xGrid * yGrid * zGrid)]
    output_string_connections = [
        "CONNECTIONS " + str((xGrid - 1) * yGrid * zGrid + xGrid * (yGrid - 1) * zGrid + xGrid * yGrid * (zGrid - 1))
    ]

    cellid_1 = 1

    for k in range(zGrid):
        zloc = (k + 0.5) * resolution

        for j in range(yGrid):
            yloc = (j + 0.5) * resolution

            for i in range(xGrid):
                xloc = (i + 0.5) * resolution

                output_string_cells.append(f"\n{cellid_1} {xloc} {yloc} {zloc} {volume}")
                cellid_1 += 1

                grid_cellid_1 = i + 1 + j * xGrid + k * xGrid * yGrid
                if i < xGrid - 1:
                    xloc_local = (i + 1) * resolution
                    cellid_2 = grid_cellid_1 + 1
                    output_string_connections.append(
                        f"\n{grid_cellid_1} {cellid_2} {xloc_local} {yloc} {zloc} {face_area}"
                    )
                if j < yGrid - 1:
                    yloc_local = (j + 1) * resolution
                    cellid_2 = grid_cellid_1 + xGrid
                    output_string_connections.append(
                        f"\n{grid_cellid_1} {cellid_2} {xloc} {yloc_local} {zloc} {face_area}"
                    )
                if k < zGrid - 1:
                    zloc_local = (k + 1) * resolution
                    cellid_2 = grid_cellid_1 + xGrid * yGrid
                    output_string_connections.append(
                        f"\n{grid_cellid_1} {cellid_2} {xloc} {yloc} {zloc_local} {face_area}"
                    )

    return output_string_cells + ["\n"] + output_string_connections


def render_borders(state: State):
    x_grid, y_grid, z_grid = cast(np.ndarray, state.general.number_cells)
    resolution = state.general.cell_resolution

    face_area = resolution**2

    output_string_east = ["CONNECTIONS " + str(y_grid * z_grid)]
    output_string_west = ["CONNECTIONS " + str(y_grid * z_grid)]

    output_string_north = ["CONNECTIONS " + str(x_grid * z_grid)]
    output_string_south = ["CONNECTIONS " + str(x_grid * z_grid)]

    yloc_south = 0
    xloc_west = 0
    yloc_north = y_grid * resolution
    xloc_east = x_grid * resolution

    for k in range(z_grid):
        zloc = (k + 0.5) * resolution

        for i in range(x_grid):
            xloc = (i + 0.5) * resolution
            cellid_north = (x_grid * (y_grid - 1)) + i + 1 + k * x_grid * y_grid
            cellid_south = i + 1 + k * x_grid * y_grid
            output_string_north.append(f"\n{cellid_north} {xloc} {yloc_north} {zloc} {face_area}")
            output_string_south.append(f"\n{cellid_south} {xloc} {yloc_south} {zloc} {face_area}")

        for j in range(y_grid):
            yloc = (j + 0.5) * resolution
            cellid_east = (j + 1) * x_grid + k * x_grid * y_grid
            cellid_west = j * x_grid + 1 + k * x_grid * y_grid
            output_string_east.append(f"\n{cellid_east} {xloc_east} {yloc} {zloc} {face_area}")
            output_string_west.append(f"\n{cellid_west} {xloc_west} {yloc} {zloc} {face_area}")

    return (output_string_north, output_string_east, output_string_south, output_string_west)
