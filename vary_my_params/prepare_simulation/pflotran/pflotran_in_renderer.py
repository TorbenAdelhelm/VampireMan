import logging
import pathlib

import jinja2

from ...config import Config
from .pflotran_generate_mesh import write_mesh_and_border_files


def render(config: Config):
    write_mesh_and_border_files(config.data, config.general.output_directory)
    logging.debug("Rendered {north,east,south,west}.ex")

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / "templates"))
    template = env.get_template("pflotran.in.j2")

    with open(f"{config.general.output_directory}/pflotran.in", "w") as file:
        file.write(template.render(config.data))
        logging.debug("Rendered pflotran.in")
