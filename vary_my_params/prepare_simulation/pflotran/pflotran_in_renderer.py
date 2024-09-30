import logging
import os
import pathlib

import jinja2

from ...config import Config, HeatPump, ParameterValueXYZ
from ...utils import get_answer
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
            if not get_answer(config, f"Should the directory {datapoint_dir} be overwritten?"):
                continue
        except OSError as error:
            logging.critical("Directory at %s could not be created, cannot proceed", datapoint_dir)
            raise error

        # Ensure hydraulic_head is x, y, z
        hydraulic_head = datapoint.data.get("hydraulic_head")
        assert hydraulic_head is not None
        if isinstance(hydraulic_head.value, float):
            hydraulic_head.value = ParameterValueXYZ(x=0, y=hydraulic_head.value, z=0)

        values = datapoint.data
        heatpumps = [{name: d.value} for name, d in datapoint.data.items() if isinstance(d.value, HeatPump)]
        values["heatpumps"] = heatpumps  # type: ignore
        values["time_to_simulate"] = config.general.time_to_simulate  # type: ignore

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
