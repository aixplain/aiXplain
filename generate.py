"""Generate the static enum, pipeline and v2 enum-include modules from backend catalog data.

The generator is split into two steps that never run together:

``python generate.py fetch``
    The only networked step. Snapshots the four backend catalog endpoints into the
    committed JSON fixtures under ``tools/generator/fixtures/``. It needs a credential
    and is run by hand when someone wants to refresh the data.

``python generate.py render`` (the default)
    Deterministic, offline and credential-free. Renders the generated modules from those
    fixtures, which is what lets CI gate on drift without a backend or a secret.

Every backend-derived value is emitted through :func:`py_literal` (never interpolated
raw), and every value used as a Python identifier is validated by :func:`py_identifier`.
A value that cannot be emitted safely fails the render instead of being mangled into a
module that every SDK user imports.
"""

import argparse
import json
import keyword
import math
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urljoin, urlparse

import requests
from jinja2 import BaseLoader, Environment

# The render path imports nothing from aixplain.*: the generated modules are what
# `import aixplain` loads, so the generator cannot depend on them. The fetch path
# imports the SDK's URL policy lazily, at the one place a key goes on the wire.

#: Repo root, so paths resolve the same no matter which directory the generator is
#: invoked from. Resolving against the CWD used to scatter an ``aixplain/`` tree
#: wherever the script happened to run (ENG-3435).
REPO_ROOT = Path(__file__).resolve().parent

ENUMS_MODULE_PATH = REPO_ROOT / "aixplain" / "v1" / "enums" / "generated_enums.py"
PIPELINE_MODULE_PATH = REPO_ROOT / "aixplain" / "v1" / "modules" / "pipeline" / "pipeline.py"
ENUMS_INCLUDE_PATH = REPO_ROOT / "aixplain" / "v2" / "enums_include.py"

#: Committed snapshots of the backend catalog. The render step reads only these.
FIXTURE_DIR = REPO_ROOT / "tools" / "generator" / "fixtures"
RUFF_CONFIG_PATH = REPO_ROOT / "ruff.toml"

#: ``sdk/<name>`` endpoints backing each fixture, and the key each one is ordered by.
ENDPOINTS = {
    "functions": "id",
    "suppliers": "code",
    "languages": "label",
    "licenses": "name",
}

DEFAULT_BACKEND_URL = "https://platform-api.aixplain.com"

SEGMENTOR_FUNCTIONS = [
    "split-on-linebreak",
    "speaker-diarization-audio",
    "voice-activity-detection",
]

RECONSTRUCTOR_FUNCTIONS = ["text-reconstruction", "audio-reconstruction"]

#: Function ids whose catalog entry lists one parameter code twice, and the attribute
#: name that pair collapses to. The backend serves the hypothesis (``name: "output"``)
#: and the reference (``name: "reference"``) of the two benchmark scorers under the
#: single code ``text``; a node class can only expose one ``text`` attribute, and the
#: pair is identical in every field the generator emits, so the first is kept and the
#: second dropped from both generated modules. Any other duplicate fails the render:
#: it may be two different parameters, and quietly keeping one of them would ship a
#: node class and a ``FunctionInputOutput`` entry that disagree.
KNOWN_DUPLICATE_PARAMETERS: Dict[str, Tuple[str, ...]] = {
    "benchmark-scoring-asr": ("text",),
    "benchmark-scoring-mt": ("text",),
}

#: Fields the templates read from every parameter, so a duplicate is only droppable
#: when the copies agree on all of them.
PARAMETER_FIELDS = ("code", "dataType", "required", "multipleValues", "defaultValues", "isFixed")
OUTPUT_FIELDS = ("code", "dataType", "defaultValue")

#: Names ``aixplain/v2/enums_include.py`` re-exports. All of them are exported by
#: ``aixplain.v1.enums``; the list is declared once so the import block and ``__all__``
#: cannot drift apart.
ENUMS_INCLUDE_NAMES = [
    "AssetStatus",
    "ErrorHandler",
    "FileType",
    "Function",
    "Language",
    "License",
    "OnboardStatus",
    "OwnershipType",
    "Privacy",
    "ResponseStatus",
    "SortBy",
    "SortOrder",
    "StorageType",
    "Supplier",
    "FunctionType",
    "EvolveType",
    "CodeInterpreterModel",
]

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

#: Width Jinja's ``wordwrap`` filter used, kept so regenerated docstrings do not
#: reflow against the committed output.
DOCSTRING_WIDTH = 79


class GeneratorValueError(ValueError):
    """A backend value cannot be emitted safely into generated Python source."""


def enumify(value: str, source: str = "backend value") -> str:
    """Slugify a string, uppercase it and validate it as an enum member name.

    Args:
        value (str): The backend value to convert.
        source (str): Human-readable origin, used in the error message.

    Returns:
        str: A valid Python identifier usable as an enum member name.

    Raises:
        GeneratorValueError: If the value cannot become a valid identifier.
    """
    slug = re.sub(r"\s+", "_", value or "")
    slug = re.sub(r"[-.]+", "_", slug)
    slug = re.sub(r"[^a-zA-Z0-9-_.]+", "", slug)
    slug = slug.upper()

    # Handle numeric-only strings by prefixing with underscore
    if slug.isdigit():
        slug = f"_{slug}"

    return py_identifier(slug, source=f"{source} {value!r}")


def py_identifier(value: Any, *, source: str) -> str:
    """Validate a value as a Python identifier, or fail the render.

    Surrounding whitespace is stripped first: the backend does serve values such as
    ``"text "`` (the OutputType of ``text-detection``), and whitespace is never part of
    an identifier, so removing it loses nothing. Anything else is rejected rather than
    rewritten.

    Args:
        value (Any): The candidate identifier.
        source (str): Human-readable origin, used in the error message.

    Returns:
        str: The stripped value, once it is known to be safe.

    Raises:
        GeneratorValueError: If the value is not a usable Python identifier.
    """
    text = value.strip() if isinstance(value, str) else ""
    if not IDENTIFIER_RE.match(text) or keyword.iskeyword(text):
        raise GeneratorValueError(
            f"{source}: {value!r} is not a usable Python identifier. "
            "Fix the value at the backend or add an explicit mapping; the generator "
            "will not mangle it into something that imports."
        )
    return text


def py_literal(value: Any) -> str:
    """Render a backend value as a Python literal.

    This is the only way any backend-derived value reaches the generated source.
    ``repr`` is used rather than ``json.dumps`` because ``json.dumps`` defaults to
    ``ensure_ascii=True`` and would rewrite the non-ASCII characters already present in
    the committed output (curly quotes) into unicode escapes.

    Args:
        value (Any): A string, number, boolean, ``None``, list or dict.

    Returns:
        str: The value as Python source.

    Raises:
        GeneratorValueError: If the value is of a type with no safe literal form.
    """
    if isinstance(value, str) or value is None or isinstance(value, bool):
        return repr(value)
    if isinstance(value, float) and not math.isfinite(value):
        # ``repr`` gives a bare ``nan``/``inf``: valid to ruff, a NameError at import.
        raise GeneratorValueError(f"Non-finite number {value!r} has no Python literal form that imports.")
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(py_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{py_literal(k)}: {py_literal(v)}" for k, v in value.items()) + "}"
    raise GeneratorValueError(f"{type(value).__name__} value {value!r} has no safe Python literal form.")


def py_docstring(value: Optional[str], indent: int = 4) -> str:
    """Escape and wrap a backend string for embedding inside a triple-quoted docstring.

    Args:
        value (Optional[str]): The backend text.
        indent (int): Column the continuation lines are indented to.

    Returns:
        str: Wrapped, escaped text safe to interpolate between triple-quote delimiters.
    """
    lines: List[str] = []
    for line in (value or "").splitlines():
        lines.extend(
            textwrap.wrap(
                line,
                width=DOCSTRING_WIDTH,
                expand_tabs=False,
                replace_whitespace=False,
                break_long_words=True,
                break_on_hyphens=True,
            )
            or [""]
        )
    # Escaping happens after wrapping: a long token broken at the wrap column can
    # then never be split between the two characters of an escaped backslash, which
    # would leave a line continuation followed by a fresh escape sequence.
    lines = [line.replace("\\", "\\\\").replace('"""', '\\"\\"\\"') for line in lines]
    if lines and lines[-1].endswith('"'):
        lines[-1] = lines[-1][:-1] + '\\"'
    return ("\n" + " " * indent).join(lines)


ENUMS_MODULE_TEMPLATE = """\"\"\"Auto-generated enum module containing static values from the backend API.\"\"\"

# This is an auto generated module. PLEASE DO NOT EDIT
# This module contains static enums that were previously loaded dynamically

from enum import Enum
from typing import Dict, Any, Tuple
from dataclasses import dataclass
from aixplain.v1.base.parameters import BaseParameters, Parameter


class Function(str, Enum):
    \"\"\"Enum representing available functions in the aiXplain platform.\"\"\"

    {% for function in functions %}
    {{ function.id|enumify("Function member for function id") }} = {{ function.id|pyrepr }}
    {% endfor %}

    def get_input_output_params(self) -> Tuple[Dict, Dict]:
        \"\"\"Get the input and output parameters for this function.

        Returns:
            Tuple[Dict, Dict]: A tuple containing (input_params, output_params).
        \"\"\"
        function_io = FunctionInputOutput.get(self.value, None)
        if function_io is None:
            return {}, {}
        input_params = {
            param["code"]: param for param in function_io["spec"]["params"]
        }
        output_params = {
            param["code"]: param for param in function_io["spec"]["output"]
        }
        return input_params, output_params

    def get_parameters(self) -> "FunctionParameters":
        \"\"\"Get a FunctionParameters object for this function.

        Returns:
            FunctionParameters: Object containing the function's parameters.
        \"\"\"
        if not hasattr(self, '_parameters') or self._parameters is None:
            input_params, _ = self.get_input_output_params()
            self._parameters = FunctionParameters(input_params)
        return self._parameters

# Static FunctionInputOutput dictionary
FunctionInputOutput = {
    {% for function in functions %}
    {{ function.id|pyrepr }}: {
        "input": {
            {% for param in function.params %}
            {% if param.required %}{{ param.dataType|pyrepr }}{% if not loop.last %}, {% endif %}{% endif %}
            {% endfor %}
        },
        "output": {
            {% for output in function.output %}
            {{ output.dataType|pyrepr }}{% if not loop.last %}, {% endif %}
            {% endfor %}
        },
        "spec": {
            "id": {{ function.id|pyrepr }},
            "name": {{ function.name|pyrepr }},
            "description": {{ function.metaData.description|pyrepr }},
            "params": [
                {% for param in function.params %}
                {
                    "code": {{ param.code|pyrepr }},
                    "dataType": {{ param.dataType|pyrepr }},
                    "required": {{ param.required|pyrepr }},
                    "multipleValues": {{ param.multipleValues|default(false)|pyrepr }},
                    "defaultValues": {{ param.defaultValues|default(none)|pyrepr }},
                    "isFixed": {{ param.isFixed|default(false)|pyrepr }}
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ],
            "output": [
                {% for output in function.output %}
                {
                    "code": {{ output.code|pyrepr }},
                    "dataType": {{ output.dataType|pyrepr }},
                    "defaultValue": {{ output.defaultValue|default(none)|pyrepr }}
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }
    }{% if not loop.last %},{% endif %}
    {% endfor %}
}

class FunctionParameters(BaseParameters):
    \"\"\"Class to store and manage function parameters.\"\"\"

    def __init__(self, input_params: Dict):
        \"\"\"Initialize FunctionParameters with input parameters.

        Args:
            input_params (Dict): Dictionary of input parameters.
        \"\"\"
        super().__init__()
        for param_code, param_config in input_params.items():
            self.parameters[param_code] = Parameter(
                name=param_code,
                required=param_config.get("required", False),
                value=None,
            )


class Supplier(Enum):
    \"\"\"Enum representing available suppliers in the aiXplain platform.\"\"\"

    {% for supplier in suppliers %}
    {{ supplier.code|enumify("Supplier member for supplier code") }} = {
        "id": {{ supplier.id|pyrepr }},
        "name": {{ supplier.name|pyrepr }},
        "code": {{ supplier.code|pyrepr }}
    }
    {% endfor %}

    def __str__(self):
        \"\"\"Return the supplier name.\"\"\"
        return self.value["name"]


class Language(Enum):
    \"\"\"Enum representing available languages in the aiXplain platform.\"\"\"

    {% for language in languages %}
    {% set language_member = language.label|enumify("Language member for language label") %}
    {{ language_member }} = {
        "language": {{ language.value|pyrepr }},
        "dialect": ""
    }
    {% for dialect in language.dialects %}
    {{ language_member }}_{{ dialect.label|enumify("Language member for dialect label") }} = {
        "language": {{ language.value|pyrepr }},
        "dialect": {{ dialect.value|pyrepr }}
    }
    {% endfor %}
    {% endfor %}


class License(str, Enum):
    \"\"\"Enum representing available licenses in the aiXplain platform.\"\"\"

    {% for license in licenses %}
    {{ license.name|enumify("License member for license name") }} = {{ license.id|pyrepr }}
    {% endfor %}

"""

PIPELINE_MODULE_TEMPLATE = """\\
\"\"\"Auto-generated pipeline module containing node classes and Pipeline factory methods.\"\"\"

# This is an auto generated module. PLEASE DO NOT EDIT


from typing import Union, Type
from aixplain.v1.enums import DataType

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
from aixplain.v1.modules import asset

{% for spec in specs %}

class {{ spec.class_name }}Inputs(Inputs):
    \"\"\"Input parameters for {{ spec.class_name }}.\"\"\"

{% for input in spec.inputs %}
    {{ input.name }}: InputParam = None
{% endfor %}

    def __init__(self, node=None):
        \"\"\"Initialize {{ spec.class_name }}Inputs.\"\"\"
        super().__init__(node=node)
{% for input in spec.inputs %}
        self.{{ input.name }} = self.create_param(
            code={{ input.code|pyrepr }},
            data_type=DataType.{{ input.data_type | upper }},
            is_required={{ input.is_required|pyrepr }}
        )
{% endfor %}


class {{ spec.class_name }}Outputs(Outputs):
    \"\"\"Output parameters for {{ spec.class_name }}.\"\"\"

{% for output in spec.outputs %}
    {{ output.name }}: OutputParam = None
{% endfor %}
{% if spec.is_segmentor %}
    audio: OutputParam = None
{% endif %}

    def __init__(self, node=None):
        \"\"\"Initialize {{ spec.class_name }}Outputs.\"\"\"
        super().__init__(node=node)
{% for output in spec.outputs %}
        self.{{ output.name }} = self.create_param(
            code={{ output.code|pyrepr }},
            data_type=DataType.{{ output.data_type | upper }}
        )
{% endfor %}
{% if spec.is_segmentor %}
        self.audio = self.create_param(code="audio", data_type=DataType.AUDIO)
{% endif %}


class {{ spec.class_name }}({{spec.base_class}}[{{ spec.class_name }}Inputs, {{ spec.class_name }}Outputs]):
    \"\"\"{{ spec.class_name }} node.

{% if spec.description|docstring(4) %}
    {{ spec.description | docstring(4) }}

{% endif %}
    InputType: {{ spec.input_type }}
    OutputType: {{ spec.output_type }}
    \"\"\"
    function: str = {{ spec.id|pyrepr }}
    input_type: str = DataType.{{ spec.input_type | upper }}
    output_type: str = DataType.{{ spec.output_type | upper }}

    inputs_class: Type[TI] = {{ spec.class_name }}Inputs
    outputs_class: Type[TO] = {{ spec.class_name }}Outputs

{% endfor %}


class Pipeline(DefaultPipeline):
    \"\"\"Pipeline class for creating and managing AI processing pipelines.\"\"\"

{% for spec in specs %}
    def {{ spec.function_name }}(self, asset_id: Union[str, asset.Asset], *args, **kwargs) -> {{ spec.class_name }}:
        \"\"\"Create a {{ spec.class_name }} node.
{% if spec.description|docstring(8) %}

        {{ spec.description | docstring(8) }}
{% endif %}
        \"\"\"
        return {{ spec.class_name }}(*args, asset_id=asset_id, pipeline=self, **kwargs)

{% endfor %}
"""

ENUMS_INCLUDE_TEMPLATE = """\"\"\"Compatibility imports for legacy enums in v2.

This is an auto generated module. PLEASE DO NOT EDIT.
\"\"\"

# Import all enums from legacy system for compatibility
from aixplain.v1.enums import (
{% for name in names %}
    {{ name }},
{% endfor %}
)

# Re-export for compatibility
__all__ = [
{% for name in names %}
    {{ name|pyrepr }},
{% endfor %}
]
"""


def get_config() -> Dict[str, Optional[str]]:
    """Get the fetch-step configuration from environment variables.

    ``TEAM_API_KEY`` takes precedence over ``AIXPLAIN_API_KEY``, the same order as
    ``aixplain.v2.core.Aixplain``, so a fetch runs under the account every other SDK
    call in the same shell uses. When both are set to different keys the SDK refuses
    to guess (``aixplain.utils.config``), and so does the generator.

    Returns:
        Dict[str, Optional[str]]: The API key and backend URL to fetch with.

    Raises:
        ValueError: If both key variables are set and disagree.
    """
    team_key = os.getenv("TEAM_API_KEY")
    aixplain_key = os.getenv("AIXPLAIN_API_KEY")
    if team_key and aixplain_key and team_key != aixplain_key:
        raise ValueError(
            "Conflicting API keys: TEAM_API_KEY and AIXPLAIN_API_KEY are both set and differ. "
            "Unset one so the fixtures are captured under the same account as every other SDK call."
        )
    return {
        "api_key": team_key or aixplain_key,
        "backend_url": os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL),
    }


def api_request(path: str) -> Any:
    """Fetch one catalog endpoint from the backend.

    Args:
        path (str): Endpoint name under ``sdk/``.

    Returns:
        Any: The decoded JSON response.

    Raises:
        ValueError: If no API key is configured, or ``BACKEND_URL`` fails the SDK's
            URL policy (``aixplain.utils.url_safety``).
    """
    # Lazy: the SDK's config-URL policy is the one gate every other request carrying
    # the key goes through, and importing it here keeps the render path SDK-free.
    from aixplain.utils.url_safety import validate_config_url

    config = get_config()
    api_key = config["api_key"]
    if not api_key:
        raise ValueError("AIXPLAIN_API_KEY (or TEAM_API_KEY) environment variable is required to fetch")
    backend_url = validate_config_url(config["backend_url"], "BACKEND_URL")

    url = urljoin(backend_url if backend_url.endswith("/") else f"{backend_url}/", f"sdk/{path}")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    r = requests.get(url, headers=headers, timeout=(10, 30))
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"{path} could not be loaded, see error below")
        raise e
    return r.json()


def display_path(path: Path) -> str:
    """Show a path relative to the repo root when it lives there, else as-is.

    Args:
        path (Path): The path.

    Returns:
        str: The shortest unambiguous form for a message.
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def fixture_path(name: str) -> Path:
    """Return the committed fixture path for an endpoint.

    Args:
        name (str): Endpoint name.

    Returns:
        Path: Path to the fixture file.
    """
    return FIXTURE_DIR / f"{name}.json"


def load_fixture(name: str) -> List[Dict[str, Any]]:
    """Load one committed fixture.

    Args:
        name (str): Endpoint name.

    Returns:
        List[Dict[str, Any]]: The snapshotted catalog items.

    Raises:
        GeneratorValueError: If the fixture is missing or contains a non-finite number.
    """
    path = fixture_path(name)
    if not path.exists():
        raise GeneratorValueError(f"Missing fixture {path}. Run `python generate.py fetch` to create it.")

    def refuse_non_finite(token: str) -> Any:
        # ``json`` accepts NaN/Infinity by default; no Python literal for them imports.
        raise GeneratorValueError(f"{display_path(path)} contains the non-finite number {token}.")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f, parse_constant=refuse_non_finite)


def stable_order(items: Sequence[Dict[str, Any]], previous: Sequence[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """Order freshly fetched items like the previous fixture, appending new ones at the end.

    The backend does not return the catalog in a stable order, so a naive refresh
    reshuffles thousands of generated lines and buries the actual change. Keeping the
    previous order makes a fixture refresh reviewable as a diff.

    Args:
        items (Sequence[Dict[str, Any]]): Freshly fetched items.
        previous (Sequence[Dict[str, Any]]): Items from the committed fixture.
        key (str): Field identifying an item across refreshes.

    Returns:
        List[Dict[str, Any]]: The fetched items in the previous fixture's order.
    """
    order = {item.get(key): index for index, item in enumerate(previous)}
    return sorted(items, key=lambda item: order.get(item.get(key), len(order)))


def fetch() -> None:
    """Snapshot the backend catalog endpoints into the committed fixtures."""
    from dotenv import load_dotenv

    # An explicit path: a bare ``load_dotenv()`` walks up parent directories, which is
    # what let a stray ``.env`` redirect the SDK's key in BUG-939.
    load_dotenv(REPO_ROOT / ".env", override=False)

    backend_url = get_config()["backend_url"]
    print(f"Fetching from {backend_url} (record this host in {display_path(FIXTURE_DIR)}/README.md)")
    if urlparse(backend_url).hostname != urlparse(DEFAULT_BACKEND_URL).hostname:
        print(
            f"WARNING: {backend_url} is not the production backend. Supplier ids are environment-specific, "
            "so committing this snapshot would rewrite every Supplier id in the shipped SDK."
        )

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for name, key in ENDPOINTS.items():
        print(f"Fetching {name}")
        payload = api_request(name)
        items = payload["items"] if isinstance(payload, dict) else payload

        path = fixture_path(name)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                items = stable_order(items, json.load(f), key)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Wrote {len(items)} {name} to {display_path(path)}")


def check_unique_members(names: Iterable[Tuple[str, str]], family: str) -> None:
    """Fail the render when two backend values collapse to the same enum member name.

    Left unchecked this surfaces as ``TypeError: Attempted to reuse key`` at import
    time, in every user's process, rather than here where a human is present.

    Args:
        names (Iterable[Tuple[str, str]]): ``(member_name, backend_value)`` pairs.
        family (str): Enum name, used in the error message.

    Raises:
        GeneratorValueError: If two values produce the same member name.
    """
    seen: Dict[str, str] = {}
    for member, value in names:
        if member in seen:
            raise GeneratorValueError(
                f"{family}.{member} would be defined twice, from {seen[member]!r} and {value!r}. "
                "Fix the colliding values at the backend or add an explicit mapping."
            )
        seen[member] = value


def describe(record: Dict[str, Any], family: str, index: int, key: str) -> str:
    """Name a catalog record for an error message.

    Args:
        record (Dict[str, Any]): The record.
        family (str): Fixture name, e.g. ``suppliers``.
        index (int): Position of the record in the fixture.
        key (str): Field that identifies the record to a human.

    Returns:
        str: e.g. ``suppliers.json[3] ('google')``.
    """
    return f"{family}.json[{index}] ({record.get(key)!r})"


def require_fields(record: Dict[str, Any], fields: Sequence[str], source: str) -> None:
    """Fail the render when a record lacks a field a template emits.

    Left unchecked, Jinja renders the hole as ``Undefined`` and the error names neither
    the field nor the record.

    Args:
        record (Dict[str, Any]): The record.
        fields (Sequence[str]): Fields that must be present and not null.
        source (str): Human-readable origin, used in the error message.

    Raises:
        GeneratorValueError: If any field is missing or null.
    """
    missing = [field for field in fields if record.get(field) is None]
    if missing:
        raise GeneratorValueError(f"{source} is missing {', '.join(repr(field) for field in missing)}.")


def validate_enum_data(
    functions: List[Dict[str, Any]],
    suppliers: List[Dict[str, Any]],
    languages: List[Dict[str, Any]],
    licenses: List[Dict[str, Any]],
) -> None:
    """Validate every backend value the enum module turns into an identifier or a literal.

    Args:
        functions (List[Dict[str, Any]]): Function catalog.
        suppliers (List[Dict[str, Any]]): Supplier catalog.
        languages (List[Dict[str, Any]]): Language catalog.
        licenses (List[Dict[str, Any]]): License catalog.
    """
    for index, supplier in enumerate(suppliers):
        require_fields(supplier, ("id", "name", "code"), describe(supplier, "suppliers", index, "code"))
    for index, license_ in enumerate(licenses):
        require_fields(license_, ("id", "name"), describe(license_, "licenses", index, "name"))
    for index, language in enumerate(languages):
        source = describe(language, "languages", index, "label")
        require_fields(language, ("label", "value"), source)
        for dialect in language.get("dialects", []):
            require_fields(dialect, ("label", "value"), f"dialect {dialect.get('label')!r} of {source}")

    check_unique_members(
        ((enumify(f["id"], "Function member for function id"), f["id"]) for f in functions), "Function"
    )
    check_unique_members(
        ((enumify(s["code"], "Supplier member for supplier code"), s["code"]) for s in suppliers), "Supplier"
    )
    check_unique_members(
        ((enumify(x["name"], "License member for license name"), x["name"]) for x in licenses), "License"
    )

    language_members: List[Tuple[str, str]] = []
    for language in languages:
        label = enumify(language["label"], "Language member for language label")
        language_members.append((label, language["label"]))
        for dialect in language.get("dialects", []):
            dialect_label = enumify(dialect["label"], "Language member for dialect label")
            language_members.append((f"{label}_{dialect_label}", f"{language['label']}/{dialect['label']}"))
    check_unique_members(language_members, "Language")


def resolve_duplicates(
    entries: List[Dict[str, Any]], fields: Sequence[str], allowed: Sequence[str], source: str
) -> List[Dict[str, Any]]:
    """Collapse entries that share an attribute name, or fail the render.

    Two entries collide when their codes strip to the same identifier, since that is
    the attribute the node class exposes. A collision is only dropped when it is listed
    in :data:`KNOWN_DUPLICATE_PARAMETERS` and the copies agree on every emitted field;
    then the first is kept, for both generated modules.

    Args:
        entries (List[Dict[str, Any]]): Parameter or output specs of one function.
        fields (Sequence[str]): Fields the templates emit for each entry.
        allowed (Sequence[str]): Attribute names whose duplication is known and accepted.
        source (str): Human-readable origin, used in the error message.

    Returns:
        List[Dict[str, Any]]: The entries with accepted duplicates removed.

    Raises:
        GeneratorValueError: On a duplicate that is not accepted, or that is accepted
            but whose copies differ.
    """
    kept: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        attribute = py_identifier(entry["code"], source=source)
        first = kept.get(attribute)
        if first is None:
            kept[attribute] = entry
            continue
        pair = f"{source}: {first['code']!r} ({first.get('name')!r}) and {entry['code']!r} ({entry.get('name')!r})"
        if attribute not in allowed:
            raise GeneratorValueError(
                f"{pair} both map to the attribute {attribute!r}. Fix the duplicate at the backend, or if the "
                "copies are one parameter served twice, list it in KNOWN_DUPLICATE_PARAMETERS."
            )
        differing = [field for field in fields if first.get(field) != entry.get(field)]
        if differing:
            raise GeneratorValueError(
                f"{pair} are listed as a known duplicate but differ in {', '.join(repr(f) for f in differing)}; "
                "dropping one would lose a real parameter."
            )
    return list(kept.values())


def prepare_functions(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate the function catalog and normalise it for both templates.

    Everything both generated modules must agree on is decided here, once: required
    fields, a null description rendered as ``""`` (what ``ModelTool`` and the agent
    payload always carried), and the duplicate-parameter policy.

    Args:
        functions (List[Dict[str, Any]]): Function catalog as fetched.

    Returns:
        List[Dict[str, Any]]: Shallow copies with the normalised ``metaData``, ``params``
            and ``output``.
    """
    prepared = []
    for index, function in enumerate(functions):
        source = describe(function, "functions", index, "id")
        require_fields(function, ("id", "name", "metaData", "params", "output"), source)
        require_fields(function["metaData"], ("InputType", "OutputType"), f"metaData of {source}")
        for param in function["params"]:
            require_fields(param, ("code", "dataType", "required"), f"parameter {param.get('code')!r} of {source}")
        for output in function["output"]:
            require_fields(output, ("code", "dataType"), f"output {output.get('code')!r} of {source}")

        allowed = KNOWN_DUPLICATE_PARAMETERS.get(function["id"], ())
        prepared.append(
            {
                **function,
                "metaData": {**function["metaData"], "description": function["metaData"].get("description") or ""},
                "params": resolve_duplicates(
                    function["params"], PARAMETER_FIELDS, allowed, f"input parameters of {source}"
                ),
                "output": resolve_duplicates(function["output"], OUTPUT_FIELDS, allowed, f"outputs of {source}"),
            }
        )
    return prepared


def populate_specs(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Populate the function class specs, validating every generated identifier.

    Args:
        functions (List[Dict[str, Any]]): Function catalog, as returned by
            :func:`prepare_functions`.

    Returns:
        List[Dict[str, Any]]: One render spec per pipeline node class.
    """
    function_class_specs = []
    for function in functions:
        # Utility functions has dynamic input parameters so they are not
        # subject to static class generation
        if function["id"] == "utilities":
            continue

        # slugify function name by trimming some special chars and
        # transforming it to snake case
        function_name = py_identifier(
            function["id"].replace("-", "_").replace("(", "_").replace(")", "_"),
            source=f"Pipeline factory method for function id {function['id']!r}",
        )
        base_class = "AssetNode"
        is_segmentor = function["id"] in SEGMENTOR_FUNCTIONS
        is_reconstructor = function["id"] in RECONSTRUCTOR_FUNCTIONS
        if is_segmentor:
            base_class = "BaseSegmentor"
        elif is_reconstructor:
            base_class = "BaseReconstructor"
        elif "metric" in function_name.split("_"):  # TODO: Advise a better distinguisher please
            base_class = "BaseMetric"

        class_name = py_identifier(
            "".join([w.title() for w in function_name.split("_")]),
            source=f"Pipeline node class for function id {function['id']!r}",
        )

        # ``name`` is the Python attribute; ``code`` stays the raw backend value because
        # it is the wire-level key ``FunctionInputOutput`` and the platform use, and the
        # two must agree or ``AssetNode._auto_populate_params`` creates a second input.
        spec = {
            "id": function["id"],
            "is_segmentor": function["id"] in SEGMENTOR_FUNCTIONS,
            "is_reconstructor": function["id"] in RECONSTRUCTOR_FUNCTIONS,
            "function_name": function_name,
            "base_class": base_class,
            "class_name": class_name,
            "description": function["metaData"]["description"],
            "input_type": py_identifier(
                function["metaData"]["InputType"], source=f"InputType of function {function['id']!r}"
            ),
            "output_type": py_identifier(
                function["metaData"]["OutputType"], source=f"OutputType of function {function['id']!r}"
            ),
            "inputs": [
                {
                    "name": py_identifier(param["code"], source=f"Input parameter of function {function['id']!r}"),
                    "code": param["code"],
                    "data_type": py_identifier(
                        param["dataType"], source=f"Input data type of function {function['id']!r}"
                    ),
                    "is_required": param["required"],
                    "is_list": param.get("multipleValues", False),
                    "default": param.get("defaultValues"),
                    "is_fixed": param.get("isFixed", False),
                }
                for param in function["params"]
            ],
            "outputs": [
                {
                    "name": py_identifier(output["code"], source=f"Output of function {function['id']!r}"),
                    "code": output["code"],
                    "data_type": py_identifier(
                        output["dataType"], source=f"Output data type of function {function['id']!r}"
                    ),
                    "default": output.get("defaultValue"),
                }
                for output in function["output"]
            ],
        }
        function_class_specs.append(spec)

    return function_class_specs


def build_environment() -> Environment:
    """Build the Jinja environment with the safe-emission filters registered.

    Returns:
        Environment: The configured environment.
    """
    env = Environment(
        loader=BaseLoader(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["enumify"] = enumify
    env.filters["pyrepr"] = py_literal
    env.filters["docstring"] = py_docstring
    return env


def render_modules() -> Dict[Path, str]:
    """Render every generated module from the committed fixtures.

    Returns:
        Dict[Path, str]: Repo path to unformatted module source.
    """
    functions = load_fixture("functions")
    suppliers = load_fixture("suppliers")
    languages = load_fixture("languages")
    licenses = load_fixture("licenses")

    functions = prepare_functions(functions)
    validate_enum_data(functions, suppliers, languages, licenses)
    specs = populate_specs(functions)
    print(f"Populating module with {len(specs)} specs")

    env = build_environment()
    return {
        PIPELINE_MODULE_PATH: env.from_string(PIPELINE_MODULE_TEMPLATE).render(specs=specs),
        ENUMS_MODULE_PATH: env.from_string(ENUMS_MODULE_TEMPLATE).render(
            functions=functions, suppliers=suppliers, languages=languages, licenses=licenses
        ),
        ENUMS_INCLUDE_PATH: env.from_string(ENUMS_INCLUDE_TEMPLATE).render(
            names=[py_identifier(name, source="Re-exported enum name") for name in ENUMS_INCLUDE_NAMES]
        ),
    }


def ruff_format(paths: Sequence[Path]) -> None:
    """Format the rendered modules with the repo's pinned ruff configuration.

    The committed output is ``ruff format``-stable, so this pass is what makes the
    render reproducible byte-for-byte -- and idempotent, since a formatted file is a
    fixed point.

    ruff is invoked as ``python -m ruff`` so it is the version pinned in the ``test``
    extra rather than whatever happens to be on ``PATH``: an unpinned formatter would
    turn a ruff release into a red drift job on an unrelated PR.

    Args:
        paths (Sequence[Path]): Files to format in place.

    Raises:
        GeneratorValueError: If ruff is not installed in the running interpreter.
    """
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--quiet", "--config", str(RUFF_CONFIG_PATH)]
        + [str(path) for path in paths],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GeneratorValueError(
            f"`{sys.executable} -m ruff format` failed with exit code {result.returncode}. "
            "The render step formats its output, so ruff must be installed in this "
            "interpreter: `pip install '.[test]'`.\n"
            f"{result.stderr.strip()}"
        )


def render_formatted() -> Dict[Path, bytes]:
    """Render and format every generated module in a scratch directory.

    Nothing tracked is touched until every module has rendered and formatted, so a
    ruff failure (not installed, or invalid Python from a bad value) cannot leave raw
    or broken output in the tree.

    Returns:
        Dict[Path, bytes]: Repo path to the formatted module content.
    """
    with tempfile.TemporaryDirectory() as tmp:
        staged: Dict[Path, Path] = {}
        for repo_path, source in render_modules().items():
            staged_path = Path(tmp) / repo_path.relative_to(REPO_ROOT)
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.write_text(source, encoding="utf-8")
            staged[repo_path] = staged_path
        ruff_format(list(staged.values()))
        return {repo_path: staged_path.read_bytes() for repo_path, staged_path in staged.items()}


def write_modules(target_root: Path) -> Dict[Path, Path]:
    """Render and format every generated module, then write them under a target root.

    Args:
        target_root (Path): Root to write under; ``REPO_ROOT`` writes in place.

    Returns:
        Dict[Path, Path]: Repo path to the file actually written.
    """
    formatted = render_formatted()
    written: Dict[Path, Path] = {}
    for repo_path, content in formatted.items():
        destination = target_root / repo_path.relative_to(REPO_ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        written[repo_path] = destination
    return written


def render(check: bool = False) -> int:
    """Render the generated modules, or check the committed ones against a fresh render.

    Args:
        check (bool): Compare instead of writing.

    Returns:
        int: Process exit code.
    """
    if not check:
        for repo_path in write_modules(REPO_ROOT):
            print(f"Writing module to file: {repo_path.relative_to(REPO_ROOT)}")
        print("Modules generated successfully")
        return 0

    drifted = [
        repo_path
        for repo_path, content in render_formatted().items()
        if not repo_path.exists() or repo_path.read_bytes() != content
    ]
    if drifted:
        for repo_path in drifted:
            print(f"Drift: {repo_path.relative_to(REPO_ROOT)} differs from a fresh render")
        print("Run `python generate.py render` and commit the result.")
        return 1

    print("Generated modules are up to date")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the generator CLI.

    Args:
        argv (Optional[Sequence[str]]): Argument list, defaulting to ``sys.argv``.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("fetch", help="Snapshot the backend catalog into the committed fixtures (needs a credential)")
    render_parser = subparsers.add_parser("render", help="Render the generated modules from the fixtures (default)")
    render_parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if the committed modules differ from a fresh render, without writing",
    )
    args = parser.parse_args(argv)

    if args.command == "fetch":
        fetch()
        return 0
    return render(check=getattr(args, "check", False))


if __name__ == "__main__":
    sys.exit(main())
