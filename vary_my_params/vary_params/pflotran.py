from ..config import Config, Data, Datapoint, DataType, Parameter, Vary


def copy_parameter(parameter: Parameter) -> Data:
    """This function simply copies all values from a `Parameter` to a `Data` object without any transformation"""
    return Data(parameter.name, parameter.data_type, parameter.value)


def vary_params(config: Config) -> Config:
    for index in range(config.general.number_datapoints):
        # TODO split into data_fixed etc
        data = {
            "time": Data("time", DataType.SCALAR, {"final_time": 27.5}),
        }

        for _, parameter in config.parameters.items():
            match parameter.vary:
                case Vary.NONE:
                    data[parameter.name] = copy_parameter(parameter)
                case Vary.SPACE:
                    # data[parameter.name] = copy_parameter(parameter)
                    pass
                case _:
                    raise ValueError()


        config.datapoints.append(Datapoint(index, data))

    return config
