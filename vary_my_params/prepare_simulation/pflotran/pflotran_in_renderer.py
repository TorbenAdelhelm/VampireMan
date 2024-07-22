import pathlib

import jinja2

from ...config import Config


def render(config: Config):
    data = {"time": {"final_time": 27.5}}

    permeability = config.data.get("permeability")
    assert permeability is not None, "Permeability is not set, cannot continue"
    permeability = permeability.get("value")
    assert permeability is not None, "Permeability value is not set, cannot continue"
    data["permeability"] = permeability

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / "templates"))

    template = env.get_template("pflotran.in.j2")
    print(template.render(data))


if __name__ == "__main__":
    render()
