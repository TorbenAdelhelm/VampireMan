import pathlib

import jinja2


def render():
    data = {"time": {"final_time": 27.5}}

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(pathlib.Path(__file__).parent / "templates"))

    template = env.get_template("pflotran.in.j2")
    print(template.render(data))


if __name__ == "__main__":
    render()
