import logging
import os


def generate_mesh():
    settings = {
        "grid": {
            # Number of cells in the grid
            "number_cells": [
                64,
                256,
                1,
            ],
            # Size of one cell in the grid, given in meters
            "cell_resolutions": [
                5,
                5,
                5,
            ],
        },
    }
    write_mesh_file(settings)


def write_mesh_file(settings: dict[str, dict[str, list[int]]], path_to_output: str = "."):
    xGrid, yGrid, zGrid = settings["grid"]["number_cells"]
    cellXWidth, cellYWidth, cellZWidth = settings["grid"]["cell_resolutions"]

    volume = cellXWidth * cellYWidth * cellZWidth
    if cellXWidth == cellYWidth == cellZWidth:
        faceArea = cellXWidth**2
    else:
        logging.error(
            "The grid is not cubic - look at create_grid_unstructured.py OR "
            + "2D case and settings.yaml depth for z is not adapted"
        )
        raise ValueError("Grid is not cubic")

    # CELLS <number of cells>
    # <cell id> <x> <y> <z> <volume>
    # ...
    # CONNECTIONS <number of connections>
    # <cell id a> <cell id b> <face center coordinate x> <face y> <face z> <area of the face>
    output_string = ["CELLS " + str(xGrid * yGrid * zGrid)]
    cellID_1 = 1
    for k in range(0, zGrid):
        zloc = (k + 0.5) * cellZWidth
        for j in range(0, yGrid):
            yloc = (j + 0.5) * cellYWidth
            for i in range(0, xGrid):
                xloc = (i + 0.5) * cellXWidth
                output_string.append(f"\n{cellID_1} {xloc} {yloc} {zloc} {volume}")
                cellID_1 += 1

    output_string.append(
        "\nCONNECTIONS " + str((xGrid - 1) * yGrid * zGrid + xGrid * (yGrid - 1) * zGrid + xGrid * yGrid * (zGrid - 1))
    )
    for k in range(0, zGrid):
        zloc = (k + 0.5) * cellZWidth
        for j in range(0, yGrid):
            yloc = (j + 0.5) * cellYWidth
            for i in range(0, xGrid):
                xloc = (i + 0.5) * cellXWidth
                cellID_1 = i + 1 + j * xGrid + k * xGrid * yGrid
                if i < xGrid - 1:
                    xloc_local = (i + 1) * cellXWidth
                    cellID_2 = cellID_1 + 1
                    output_string.append(f"\n{cellID_1} {cellID_2} {xloc_local} {yloc} {zloc} {faceArea}")
                if j < yGrid - 1:
                    yloc_local = (j + 1) * cellYWidth
                    cellID_2 = cellID_1 + xGrid
                    output_string.append(f"\n{cellID_1} {cellID_2} {xloc} {yloc_local} {zloc} {faceArea}")
                if k < zGrid - 1:
                    zloc_local = (k + 1) * cellZWidth
                    cellID_2 = cellID_1 + xGrid * yGrid
                    output_string.append(f"\n{cellID_1} {cellID_2} {xloc} {yloc} {zloc_local} {faceArea}")

    if not os.path.exists(path_to_output):
        os.makedirs(path_to_output)

    with open(str(path_to_output) + "/mesh.uge", "w") as file:
        file.writelines(output_string)


if __name__ == "__main__":
    generate_mesh()
