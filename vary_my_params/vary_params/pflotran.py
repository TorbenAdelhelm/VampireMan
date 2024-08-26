import numpy as np

from ..config import Config, Data, Datapoint, DataType, HeatPump, Parameter, ParameterHeatPump, Vary
from ..utils import random_nd_array
from .vary_perlin import create_const_field, create_vary_field


def copy_parameter(parameter: Parameter) -> Data:
    """This function simply copies all values from a `Parameter` to a `Data` object without any transformation"""
    return Data(parameter.name, parameter.data_type, parameter.value)


def vary_heatpump(config: Config, parameter: ParameterHeatPump) -> Data:
    resolution = np.array(config.general.cell_resolution.value)
    number_cells = np.array(config.general.number_cells.value)

    hp = parameter.value
    result_location = np.zeros(3)

    # XXX is this needed?
    match parameter.vary:
        case Vary.CONST:
            result_location = (number_cells - 1) * random_nd_array(config, 3) * resolution + (resolution * 0.5)
        case Vary.NONE:
            result_location = (np.array(hp.location) - 1) * resolution + (resolution * 0.5)
        case _:
            raise NotImplementedError()

    return Data(
        parameter.name, parameter.data_type, HeatPump(result_location.tolist(), hp.injection_temp, hp.injection_rate)
    )


def vary_params(config: Config) -> Config:
    # for step in config.steps:
    #     filter over params where step == param.step
    for index in range(config.general.number_datapoints):
        # TODO split into data_fixed etc
        data = {
            "time": Data("time", DataType.STRUCT, {"final_time": 27.5}),
        }

        for _, parameter in config.parameters.items():
            match parameter.vary:
                case Vary.NONE:
                    match parameter.data_type:
                        case DataType.HEATPUMP:
                            data[parameter.name] = vary_heatpump(config, parameter)  # type: ignore
                        case _:
                            data[parameter.name] = copy_parameter(parameter)
                case Vary.SPACE:
                    match parameter.data_type:
                        case DataType.SCALAR:
                            assert isinstance(parameter.value, float)
                            field = create_const_field(config, parameter.value)
                        case DataType.PERLIN:
                            field = create_vary_field(config, parameter)
                        case _:
                            raise NotImplementedError()
                    data[parameter.name] = Data(parameter.name, parameter.data_type, field)
                # TODO make this less copy paste
                case Vary.CONST:
                    match parameter.data_type:
                        case DataType.HEATPUMP:
                            data[parameter.name] = vary_heatpump(config, parameter)  # type: ignore
                        case _:
                            raise NotImplementedError()
                case _:
                    raise ValueError()

        config.datapoints.append(Datapoint(index, data))

    return config
