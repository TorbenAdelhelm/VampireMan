import logging
from pathlib import Path

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
    with open(f"{output_dir}/{file_name}", "w") as file:
        file.writelines(output_strings)


def render_mesh(state: State) -> list[str]:
    xGrid, yGrid, zGrid = state.general.number_cells
    resolution = state.general.cell_resolution

    volume = resolution**3
    faceArea = resolution**2

    # CELLS <number of cells>
    # <cell id> <x> <y> <z> <volume>
    # ...
    # CONNECTIONS <number of connections>
    # <cell id a> <cell id b> <face center coordinate x> <face y> <face z> <area of the face>

    output_string_cells = ["CELLS " + str(xGrid * yGrid * zGrid)]
    output_string_connections = [
        "CONNECTIONS " + str((xGrid - 1) * yGrid * zGrid + xGrid * (yGrid - 1) * zGrid + xGrid * yGrid * (zGrid - 1))
    ]

    cellID_1 = 1

    for k in range(zGrid):
        zloc = (k + 0.5) * resolution

        for j in range(yGrid):
            yloc = (j + 0.5) * resolution

            for i in range(xGrid):
                xloc = (i + 0.5) * resolution

                output_string_cells.append(f"\n{cellID_1} {xloc} {yloc} {zloc} {volume}")
                cellID_1 += 1

                gridCellID_1 = i + 1 + j * xGrid + k * xGrid * yGrid
                if i < xGrid - 1:
                    xloc_local = (i + 1) * resolution
                    cellID_2 = gridCellID_1 + 1
                    output_string_connections.append(
                        f"\n{gridCellID_1} {cellID_2} {xloc_local} {yloc} {zloc} {faceArea}"
                    )
                if j < yGrid - 1:
                    yloc_local = (j + 1) * resolution
                    cellID_2 = gridCellID_1 + xGrid
                    output_string_connections.append(
                        f"\n{gridCellID_1} {cellID_2} {xloc} {yloc_local} {zloc} {faceArea}"
                    )
                if k < zGrid - 1:
                    zloc_local = (k + 1) * resolution
                    cellID_2 = gridCellID_1 + xGrid * yGrid
                    output_string_connections.append(
                        f"\n{gridCellID_1} {cellID_2} {xloc} {yloc} {zloc_local} {faceArea}"
                    )

    return output_string_cells + ["\n"] + output_string_connections


def render_borders(state: State):
    xGrid, yGrid, zGrid = state.general.number_cells
    resolution = state.general.cell_resolution

    faceArea = resolution**2

    output_string_east = ["CONNECTIONS " + str(yGrid * zGrid)]
    output_string_west = ["CONNECTIONS " + str(yGrid * zGrid)]

    output_string_north = ["CONNECTIONS " + str(xGrid * zGrid)]
    output_string_south = ["CONNECTIONS " + str(xGrid * zGrid)]

    yloc_south = 0
    xloc_west = 0
    yloc_north = yGrid * resolution
    xloc_east = xGrid * resolution

    for k in range(zGrid):
        zloc = (k + 0.5) * resolution

        for i in range(xGrid):
            xloc = (i + 0.5) * resolution
            cellID_north = (xGrid * (yGrid - 1)) + i + 1 + k * xGrid * yGrid
            cellID_south = i + 1 + k * xGrid * yGrid
            output_string_north.append(f"\n{cellID_north} {xloc} {yloc_north} {zloc} {faceArea}")
            output_string_south.append(f"\n{cellID_south} {xloc} {yloc_south} {zloc} {faceArea}")

        for j in range(yGrid):
            yloc = (j + 0.5) * resolution
            cellID_east = (j + 1) * xGrid + k * xGrid * yGrid
            cellID_west = j * xGrid + 1 + k * xGrid * yGrid
            output_string_east.append(f"\n{cellID_east} {xloc_east} {yloc} {zloc} {faceArea}")
            output_string_west.append(f"\n{cellID_west} {xloc_west} {yloc} {zloc} {faceArea}")

    return (output_string_north, output_string_east, output_string_south, output_string_west)
