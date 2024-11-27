import pathlib

import requests
from urllib.parse import urljoin
from jinja2 import Environment, BaseLoader

from aixplain.utils import config

SEGMENTOR_FUNCTIONS = [
    "split-on-linebreak",
    "speaker-diarization-audio",
    "voice-activity-detection",
]

RECONSTRUCTOR_FUNCTIONS = ["text-reconstruction", "audio-reconstruction"]

MODULE_NAME = "pipeline"
TEMPLATE = """# This is an auto generated module. PLEASE DO NOT EDIT


from typing import Union, Type
from aixplain.enums import DataType

from .designer import (
    InputParam,
    OutputParam,
    Inputs,
    Outputs,
    TI,
    TO,
    AssetNode,
    BaseReconstructor,
    BaseSegmentor,
    BaseMetric
)
from .default import DefaultPipeline
from aixplain.modules import asset

{% for spec in specs %}

class {{ spec.class_name }}Inputs(Inputs):
{% for input in spec.inputs %}
    {{ input.name }}: InputParam = None
{% endfor %}

    def __init__(self, node=None):
        super().__init__(node=node)
{% for input in spec.inputs %}
        self.{{ input.name }} = self.create_param(code="{{ input.name }}", data_type=DataType.{{ input.data_type | upper }}, is_required={{ input.is_required }})
{% endfor %}


class {{ spec.class_name }}Outputs(Outputs):
{% for output in spec.outputs %}
    {{ output.name }}: OutputParam = None
{% endfor %}
{% if spec.is_segmentor %}
    audio: OutputParam = None
{% endif %}

    def __init__(self, node=None):
        super().__init__(node=node)
{% for output in spec.outputs %}
        self.{{ output.name }} = self.create_param(code="{{ output.name }}", data_type=DataType.{{ output.data_type | upper }})
{% endfor %}
{% if spec.is_segmentor %}
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)
{% endif %}


class {{ spec.class_name }}({{spec.base_class}}[{{ spec.class_name }}Inputs, {{ spec.class_name }}Outputs]):
    \"\"\"
    {{ spec.description | wordwrap }}

    InputType: {{ spec.input_type }}
    OutputType: {{ spec.output_type }}
    \"\"\"
    function: str = "{{ spec.id }}"
    input_type: str = DataType.{{ spec.input_type | upper }}
    output_type: str = DataType.{{ spec.output_type | upper }}

    inputs_class: Type[TI] = {{ spec.class_name }}Inputs
    outputs_class: Type[TO] = {{ spec.class_name }}Outputs

{% endfor %}


class Pipeline(DefaultPipeline):

{% for spec in specs %}
    def {{ spec.function_name }}(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> {{ spec.class_name }}:
        \"\"\"
        {{ spec.description | wordwrap }}
        \"\"\"
        return {{ spec.class_name }}(*args, asset_id=asset_id, pipeline=self, **kwargs)

{% endfor %}
"""


def fetch_functions():
    """
    Fetch functions from the backend
    """
    api_key = config.TEAM_API_KEY
    aixplain_key = config.AIXPLAIN_API_KEY
    backend_url = config.BACKEND_URL

    url = urljoin(backend_url, "sdk/functions")
    headers = {
        "Content-Type": "application/json",
    }

    if aixplain_key:
        headers["x-aixplain-key"] = aixplain_key
    else:
        headers["x-api-key"] = api_key

    r = requests.get(url, headers=headers)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print("Functions could not be loaded, see error below")
        raise e

    resp = r.json()
    return resp["items"]


def populate_data_types(functions: list):
    """
    Populate the data types
    """
    data_types = set()
    for function in functions:
        for param in function["params"]:
            data_types.add(param["dataType"])
        for output in function["output"]:
            data_types.add(output["dataType"])
    return data_types


def populate_specs(functions: list):
    """
    Populate the function class specs
    """
    function_class_specs = []
    for function in functions:
        # slugify function name by trimming some special chars and
        # transforming it to snake case
        function_name = (
            function["id"]
            .replace("-", "_")
            .replace("(", "_")
            .replace(")", "_")
        )
        base_class = "AssetNode"
        is_segmentor = function["id"] in SEGMENTOR_FUNCTIONS
        is_reconstructor = function["id"] in RECONSTRUCTOR_FUNCTIONS
        if is_segmentor:
            base_class = "BaseSegmentor"
        elif is_reconstructor:
            base_class = "BaseReconstructor"
        elif "metric" in function_name.split("_"):  # noqa: Advise a better distinguisher please
            base_class = "BaseMetric"

        spec = {
            "id": function["id"],
            "is_segmentor": function["id"] in SEGMENTOR_FUNCTIONS,
            "is_reconstructor": function["id"] in RECONSTRUCTOR_FUNCTIONS,
            "function_name": function_name,
            "base_class": base_class,
            "class_name": "".join(
                [w.title() for w in function_name.split("_")]
            ),
            "description": function["metaData"]["description"],
            "input_type": function["metaData"]["InputType"],
            "output_type": function["metaData"]["OutputType"],
            "inputs": [
                {
                    "name": param["code"],
                    "data_type": param["dataType"],
                    "is_required": param["required"],
                    "is_list": param.get("multipleValues", False),
                    "default": param.get("defaultValues"),
                    "is_fixed": param.get("isFixed", False),
                }
                for param in function["params"]
            ],
            "outputs": [
                {
                    "name": output["code"],
                    "data_type": output["dataType"],
                    "default": output.get("defaultValue"),
                }
                for output in function["output"]
            ],
        }

        function_class_specs.append(spec)

    return function_class_specs


if __name__ == "__main__":
    print("Fetching function specs")

    functions = fetch_functions()
    data_types = populate_data_types(functions)
    specs = populate_specs(functions)

    print(
        f"Populating module with {len(data_types)} data types and {len(specs)} specs"
    )
    env = Environment(
        loader=BaseLoader(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.from_string(TEMPLATE)
    output = template.render(data_types=data_types, specs=specs)

    current_dir = pathlib.Path(__file__).parent
    file_path = current_dir / f"{MODULE_NAME}.py"

    print(f"Writing module to file: {file_path}")
    with open(file_path, "w") as f:
        f.write(output)

    print("Module generated successfully")
