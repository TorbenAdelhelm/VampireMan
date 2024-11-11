from json import dumps, loads

from vary_my_params.config import Config

# This is needed as pydantic outputs additionalProperties: false instead of an empty object
json_string = dumps(Config.model_json_schema())
json_string = json_string.replace('"additionalProperties": false,', '"additionalProperties": {},')
json_dict = loads(json_string)

print(dumps(json_dict, indent=2))
