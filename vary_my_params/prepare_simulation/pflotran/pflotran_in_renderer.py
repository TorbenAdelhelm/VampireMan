import logging
import pathlib

import jinja2

from ...config import Config
from .pflotran_generate_mesh import write_mesh_and_border_files


def render(config: Config):
    data = {"time": {"final_time": 27.5}}

    permeability = config.data.get("permeability")
    assert permeability is not None, "Permeability is not set, cannot continue"
    permeability = permeability.get("value")
    assert permeability is not None, "Permeability value is not set, cannot continue"
    data["permeability"] = permeability

    data["number_cells"] = config.data.get("number_cells").get("value")
    data["cell_resolution"] = config.data.get("cell_resolution").get("value")

    write_mesh_and_border_files(data, config.general.get("output_directory", "."))
    logging.debug("Rendered {north,east,south,west}.ex")

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / "templates"))
    template = env.get_template("pflotran.in.j2")

    with open(f"{config.general.get("output_directory", ".")}/pflotran.in", "w") as file:
        file.write(template.render(data))
        logging.debug("Rendered pflotran.in")
