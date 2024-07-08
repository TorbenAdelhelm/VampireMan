import jinja2


def render():
    env = jinja2.Environment(loader=jinja2.PackageLoader("vary_my_params.prepare_simulation.pflotran"))

    template = env.get_template("pflotran.in.j2")
    print(template.render())
