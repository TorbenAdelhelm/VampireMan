from ..config import Config, Data, Datapoint, DataType, Parameter, Vary
from .vary_perlin import create_const_field, create_vary_field


def copy_parameter(parameter: Parameter) -> Data:
    """This function simply copies all values from a `Parameter` to a `Data` object without any transformation"""
    return Data(parameter.name, parameter.data_type, parameter.value)


def vary_params(config: Config) -> Config:
    for index in range(config.general.number_datapoints):
        # TODO split into data_fixed etc
        data = {
            "time": Data("time", DataType.STRUCT, {"final_time": 27.5}),
        }

        for _, parameter in config.parameters.items():
            match parameter.vary:
                case Vary.NONE:
                    data[parameter.name] = copy_parameter(parameter)
                case Vary.SPACE:
                    match parameter.data_type:
                        case DataType.SCALAR:
                            field = create_const_field(config, parameter)
                        case DataType.PERLIN:
                            field = create_vary_field(config, parameter)
                        case _:
                            raise NotImplementedError()
                    data[parameter.name] = Data(parameter.name, parameter.data_type, field)
                case _:
                    raise ValueError()

        config.datapoints.append(Datapoint(index, data))

    return config
