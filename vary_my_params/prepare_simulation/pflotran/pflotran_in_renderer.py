import logging
import pathlib

import jinja2

from ...config import Config, HeatPump, ValueXYZ
from ...vary_params.vary_perlin import create_const_field
from .pflotran_generate_mesh import write_mesh_and_border_files
from .pflotran_write_permeability import save_vary_field


def render(config: Config):
    """Render all files needed for pflotran to run. This means, `write_mesh_and_border_files`, rendering the
    pflotran.in file and rendering the permeability field with `save_vary_field`.
    """

    write_mesh_and_border_files(config, config.general.output_directory)

    LoggingUndefined = jinja2.make_logging_undefined(logger=logging.getLogger())
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / "templates"), undefined=LoggingUndefined
    )
    template = env.get_template("pflotran.in.j2")

    for index, datapoint in enumerate(config.datapoints):
        datapoint_dir = config.general.output_directory / f"datapoint-{index}"

        # Ensure hydraulic_head is x, y, z
        hydraulic_head = datapoint.data["hydraulic_head"]
        if isinstance(hydraulic_head.value, float):
            hydraulic_head.value = ValueXYZ(x=0, y=hydraulic_head.value, z=0)

        # Handle permeability
        permeability = datapoint.data["permeability"]

        # Is the permeability already a 3d field? If not, create one
        if isinstance(permeability.value, float):
            permeability.value = create_const_field(config, permeability.value)

        save_vary_field(
            datapoint_dir / "permeability_field.h5",
            config.general.number_cells,
            permeability.value,
            permeability.name,
        )

        heatpumps = [{name: d.value} for name, d in datapoint.data.items() if isinstance(d.value, HeatPump)]

        values = datapoint.data
        values["heatpumps"] = heatpumps  # type: ignore
        values["time_to_simulate"] = config.general.time_to_simulate  # type: ignore

        with open(f"{datapoint_dir}/pflotran.in", "w") as file:
            file.write(template.render(values))
            logging.debug("Rendered pflotran-%s.in", index)
