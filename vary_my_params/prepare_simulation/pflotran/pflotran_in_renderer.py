import logging
import os
import pathlib

import jinja2

from ...config import Config, DataType
from .pflotran_generate_mesh import write_mesh_and_border_files
from .pflotran_write_permeability import plot_vary_field, save_vary_field


def render(config: Config):
    write_mesh_and_border_files(config, config.general.output_directory)

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / "templates"))
    template = env.get_template("pflotran.in.j2")

    for index, datapoint in enumerate(config.datapoints):
        datapoint_dir = config.general.output_directory / f"datapoint-{index}"
        try:
            os.mkdir(datapoint_dir)
        except FileExistsError:
            logging.warning("The directory %s already exists, will override the contents", datapoint_dir)
        except OSError as error:
            logging.critical("Directory at %s could not be created, cannot proceed", datapoint_dir)
            raise error

        values = datapoint.data
        heatpumps = [{name: d.value} for name, d in datapoint.data.items() if d.data_type == DataType.HEATPUMP]
        values["heatpumps"] = heatpumps

        with open(f"{datapoint_dir}/pflotran.in", "w") as file:
            file.write(template.render(values))
            logging.debug("Rendered pflotran-%s.in", index)

        # TODO move this to ensure config
        # Raise if permeability is not in data
        permeability = datapoint.data["permeability"]

        save_vary_field(
            datapoint_dir / "permeability_field.h5",
            config.general.number_cells,
            permeability.value,
            "permeability",
        )
        plot_vary_field(permeability.value, datapoint_dir / f"{permeability.name}_field", permeability.name)
