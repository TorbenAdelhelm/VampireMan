import numpy as np

from ..config import Config, Data, Datapoint, DataType, HeatPump, Parameter, Vary
from .vary_perlin import create_const_field, create_vary_field


def copy_parameter(parameter: Parameter) -> Data:
    """This function simply copies all values from a `Parameter` to a `Data` object without any transformation"""
    return Data(name=parameter.name, data_type=parameter.data_type, value=parameter.value)


def vary_heatpump(config: Config, parameter: Parameter) -> Data:
    resolution = np.array(config.general.cell_resolution)
    number_cells = np.array(config.general.number_cells)

    hp = parameter.value
    assert isinstance(hp, HeatPump)
    result_location = np.zeros(3)

    # This is needed as we need to calculate the heatpump coordinates for pflotran.in
    match parameter.vary:
        case Vary.FIXED:
            result_location = (np.array(hp.location) - 1) * resolution + (resolution * 0.5)
        case Vary.SPACE:
            result_location = (number_cells - 1) * config.get_rng().random(3) * resolution + (resolution * 0.5)
        case _:
            raise NotImplementedError()

    return Data(
        name=parameter.name,
        data_type=parameter.data_type,
        value=HeatPump(
            location=result_location.tolist(), injection_temp=hp.injection_temp, injection_rate=hp.injection_rate
        ),
    )


def vary_parameter(config: Config, parameter: Parameter, index: int) -> Data:
    match parameter.vary:
        case Vary.FIXED:
            match parameter.data_type:
                case DataType.HEATPUMP:
                    return vary_heatpump(config, parameter)
                case _:
                    return copy_parameter(parameter)
        case Vary.SPACE:
            match parameter.data_type:
                case DataType.SCALAR:
                    assert isinstance(parameter.value, float)
                    field = create_const_field(config, parameter.value)
                case DataType.PERLIN:
                    field = create_vary_field(config, parameter)
                case DataType.HEATPUMP:
                    return vary_heatpump(config, parameter)
                case _:
                    raise NotImplementedError()
            return Data(name=parameter.name, data_type=parameter.data_type, value=field)
        # TODO make this less copy paste
        case Vary.CONST:
            match parameter.data_type:
                case DataType.ARRAY:
                    # TODO: what needs to be done here?
                    assert isinstance(parameter.value, dict)
                    max_pressure = parameter.value["max"]
                    min_pressure = parameter.value["min"]
                    assert isinstance(max_pressure, float)
                    assert isinstance(min_pressure, float)
                    distance = max_pressure - min_pressure
                    step_width = distance / config.general.number_datapoints
                    value = min_pressure + step_width * index
                    return Data(
                        name=parameter.name,
                        data_type=parameter.data_type,
                        value=create_const_field(config, value),
                    )
                case DataType.SCALAR:
                    return copy_parameter(parameter)
                case _:
                    raise NotImplementedError()
        case _:
            raise ValueError()


def vary_params(config: Config) -> Config:
    # for step in config.steps:
    #     filter over params where step == param.step
    for datapoint_index in range(config.general.number_datapoints):
        data = {}

        for _, parameter in config.hydrogeological_parameters.items():
            parameter_data = vary_parameter(config, parameter, datapoint_index)
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        for _, parameter in config.heatpump_parameters.items():
            parameter_data = vary_parameter(config, parameter, datapoint_index)
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        # TODO: do we need to shuffle the datapoints for each parameter here?
        # TODO split into data_fixed etc
        config.datapoints.append(Datapoint(index=datapoint_index, data=data))

    return config
