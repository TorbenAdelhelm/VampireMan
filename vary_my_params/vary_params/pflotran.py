import logging

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


def vary_parameter(config: Config, parameter: Parameter, index: int) -> Data | None:
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
                case DataType.HEATPUMPS:
                    return None
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


def prepare_heatpumps(config: Config):
    heatpumps_to_generate = [d for name, d in config.heatpump_parameters.items() if d.data_type == DataType.HEATPUMPS]
    heatpumps = [{name: d} for name, d in config.heatpump_parameters.items() if d.data_type == DataType.HEATPUMP]

    # TODO: Prevent naming clashes in the generated vs given heatpumps
    if len(heatpumps_to_generate) > 0 and len(heatpumps) > 0:
        logging.warn("Heatpumps will be generated and there are also given heatpumps. Check for naming clashes!")

    rand = config.get_rng()
    for hps in heatpumps_to_generate:
        # TODO: calculate relevant parameters
        assert isinstance(hps.value, dict)
        for index in range(int(hps.value["number"])):  # type:ignore
            injection_temp_min = hps.value["injection_temp_min"]
            injection_temp_max = hps.value["injection_temp_max"]
            injection_rate_min = hps.value["injection_rate_min"]
            injection_rate_max = hps.value["injection_rate_max"]

            assert isinstance(injection_temp_min, float)
            assert isinstance(injection_temp_max, float)
            assert isinstance(injection_rate_min, float)
            assert isinstance(injection_rate_max, float)

            location = np.ceil(rand.random(3) * config.general.number_cells).tolist()
            injection_temp = injection_temp_max - (rand.random() * (injection_temp_max - injection_temp_min))
            injection_rate = injection_rate_max - (rand.random() * (injection_rate_max - injection_rate_min))
            logging.debug(
                "Generating heatpump with location %s, injection_temp %s, injection_rate %s",
                location,
                injection_temp,
                injection_rate,
            )
            name = f"{hps.name}_{index}"
            config.heatpump_parameters[name] = Parameter(
                name=name,
                data_type=DataType.HEATPUMP,
                value=HeatPump(location=location, injection_temp=injection_temp, injection_rate=injection_rate),
            )

    # XXX: Here leftoff


def vary_params(config: Config) -> Config:
    # for step in config.steps:
    #     filter over params where step == param.step
    prepare_heatpumps(config)

    for datapoint_index in range(config.general.number_datapoints):
        data = {}

        for _, parameter in config.hydrogeological_parameters.items():
            parameter_data = vary_parameter(config, parameter, datapoint_index)
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        for _, parameter in config.heatpump_parameters.items():
            parameter_data = vary_parameter(config, parameter, datapoint_index)
            if parameter_data is None:
                continue
            # XXX: Store this in the parameter?
            # parameter.set_datapoint(datapoint_index, parameter_data)

            data[parameter.name] = parameter_data

        # TODO: do we need to shuffle the datapoints for each parameter here?
        # TODO split into data_fixed etc
        config.datapoints.append(Datapoint(index=datapoint_index, data=data))

    return config
