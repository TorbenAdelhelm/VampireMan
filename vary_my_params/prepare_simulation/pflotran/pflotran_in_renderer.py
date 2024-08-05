import logging
import os
import pathlib

import jinja2

from ...config import Config
from .pflotran_generate_mesh import write_mesh_and_border_files


def render(config: Config):
    write_mesh_and_border_files(config.parameters, config.general.output_directory)
    logging.debug("Rendered {north,east,south,west}.ex")

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / "templates"))
    template = env.get_template("pflotran.in.j2")

    for index, datapoint in enumerate(config.datapoints):
        datapoint_dir = config.general.output_directory / f"datapoint-{index}"
        try:
            os.mkdir(datapoint_dir)
        except FileExistsError:
            logging.warning("The directory %s already exists, will override the contents", datapoint_dir)
        with open(f"{datapoint_dir}/pflotran.in", "w") as file:
            file.write(template.render(datapoint))
            logging.debug("Rendered pflotran-%s.in", index)
