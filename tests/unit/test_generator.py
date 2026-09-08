"""Guard: generate.py is the source of truth for the generated modules (ENG-3435).

`generate.py` wrote to `aixplain/enums/` and `aixplain/modules/`, two directories the
v1 reorg deleted, so the 11,606 lines it owns -- `aixplain/v1/enums/generated_enums.py`
and `aixplain/v1/modules/pipeline/pipeline.py`, both stamped "PLEASE DO NOT EDIT" --
were hand-maintained with no working generator behind them. On a clean checkout the
write raised `FileNotFoundError`; on a machine still carrying `__pycache__` residue at
the old paths it silently succeeded and wrote 11k lines into a gitignored directory.

Fixing the write path also re-arms a latent injection hole: backend strings used to be
interpolated into Python source raw, with `escape_quotes` replacing `"` and nothing
else. So the load-bearing assertions here are:

* rendering from the committed fixtures reproduces the committed modules byte-for-byte
  -- the proof the generator, not a human, owns those files;
* a hostile backend value renders to valid, inert Python;
* a value that cannot be a Python identifier fails the render instead of shipping a
  broken module to every SDK user.

Everything runs offline from `tools/generator/fixtures/`: no network, no credentials.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import textwrap
import warnings
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:  # `tomllib` is 3.11+; CI runs 3.9. See the `test` extra in pyproject.toml.
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"


def _load_generator():
    """Import the root-level generate.py as a module.

    Returns:
        module: The imported generator.
    """
    spec = importlib.util.spec_from_file_location("aixplain_generate", REPO_ROOT / "generate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generate = _load_generator()


#: A supplier name that would execute code if it were interpolated raw into a module
#: every SDK user imports. `{sentinel}` is filled in per test with a path the payload
#: would create; the test then asserts that path does not exist.
INJECTION_PAYLOAD = 'x"""; import os; os.system("touch {sentinel}") #'


def _synthetic_dataset(payload: str = "a harmless description"):
    """Build a fixture set exercising every template path.

    Args:
        payload (str): Text to place in the value slots a hostile backend controls.

    Returns:
        dict: Endpoint name to fixture items.
    """
    functions = [
        {
            "id": "text-generation",
            "name": payload,
            "metaData": {"description": payload, "InputType": "text", "OutputType": "text"},
            "params": [
                {"code": "text", "dataType": "text", "required": True, "defaultValues": None},
                {
                    "code": "language",
                    "dataType": "label",
                    "required": False,
                    "multipleValues": True,
                    "defaultValues": ["en", payload],
                    "isFixed": True,
                },
            ],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
        # Segmentor, reconstructor and metric each select a different base class.
        {
            "id": "split-on-linebreak",
            "name": "Split On Linebreak",
            "metaData": {
                "description": 'The "Split On Linebreak" function.',
                "InputType": "text",
                "OutputType": "text",
            },
            "params": [{"code": "text", "dataType": "text", "required": True}],
            "output": [{"code": "data", "dataType": "text", "defaultValue": []}],
        },
        {
            "id": "text-reconstruction",
            "name": "Text Reconstruction",
            "metaData": {"description": "", "InputType": "text", "OutputType": "text"},
            "params": [{"code": "text", "dataType": "text", "required": True}],
            "output": [{"code": "data", "dataType": "text", "defaultValue": None}],
        },
        {
            "id": "benchmark-scoring-mt",
            "name": "Benchmark Scoring Mt",
            "metaData": {"description": "A metric.", "InputType": "text", "OutputType": "label "},
            "params": [
                {"code": "text", "name": "output", "dataType": "text", "required": True},
                # The catalog does serve a duplicated parameter code; see ENG-3435.
                {"code": "text", "name": "reference", "dataType": "text", "required": True},
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
        # Every KNOWN_DUPLICATE_PARAMETERS entry must be exercised, so the second
        # scorer is here too.
        {
            "id": "benchmark-scoring-asr",
            "name": "Benchmark Scoring Asr",
            "metaData": {"description": "A metric.", "InputType": "audio", "OutputType": "label"},
            "params": [
                {"code": "input", "name": "input", "dataType": "audio", "required": True},
                {"code": "text", "name": "output", "dataType": "text", "required": True},
                {"code": "text", "name": "reference", "dataType": "text", "required": True},
            ],
            "output": [{"code": "data", "dataType": "label", "defaultValue": None}],
        },
        # Utility functions are skipped by the pipeline template.
        {
            "id": "utilities",
            "name": "Utilities",
            "metaData": {"description": "", "InputType": "text", "OutputType": "text"},
            "params": [],
            "output": [],
        },
    ]
    return {
        "functions": functions,
        "suppliers": [
            {"id": 1, "name": "aixplain", "code": "aixplain"},
            {"id": 2, "name": payload, "code": "hostile-supplier"},
        ],
        "languages": [
            {"label": "English", "value": "en", "dialects": [{"label": "United States", "value": "en-US"}]},
            {"label": "Arabic", "value": "ar", "dialects": []},
        ],
        "licenses": [{"id": "license-id", "name": "MIT"}],
    }


def _write_fixtures(directory: Path, dataset) -> None:
    """Write a fixture set to disk.

    Args:
        directory (Path): Fixture directory to populate.
        dataset (dict): Endpoint name to items.
    """
    directory.mkdir(parents=True, exist_ok=True)
    for name, items in dataset.items():
        (directory / f"{name}.json").write_text(json.dumps(items, indent=2), encoding="utf-8")


def _render_synthetic(tmp_path: Path, monkeypatch, dataset) -> dict:
    """Render every module from a synthetic fixture set.

    Args:
        tmp_path (Path): Temporary directory.
        monkeypatch: pytest monkeypatch fixture.
        dataset (dict): Endpoint name to items.

    Returns:
        dict: Repo path to the rendered file.
    """
    _write_fixtures(tmp_path / "fixtures", dataset)
    monkeypatch.setattr(generate, "FIXTURE_DIR", tmp_path / "fixtures")
    return generate.write_modules(tmp_path / "out")


def _executable_statements(source: str) -> str:
    """Return the module's code with every string literal blanked out.

    Args:
        source (str): Rendered module source.

    Returns:
        str: The same source with string constants replaced by a placeholder, so an
            assertion can tell inert data from executable code.
    """

    class _Blank(ast.NodeTransformer):
        def visit_Constant(self, node):  # noqa: D102 - visitor
            if isinstance(node.value, str):
                return ast.copy_location(ast.Constant(value="<string>"), node)
            return node

    return ast.unparse(_Blank().visit(ast.parse(source)))


GENERATED_MODULES = [
    generate.ENUMS_MODULE_PATH,
    generate.PIPELINE_MODULE_PATH,
    generate.ENUMS_INCLUDE_PATH,
]


@pytest.mark.parametrize("module_path", GENERATED_MODULES, ids=lambda p: p.name)
def test_render_reproduces_the_committed_modules(tmp_path, module_path):
    """A render from the committed fixtures equals the committed module byte-for-byte."""
    rendered = generate.write_modules(tmp_path)[module_path]
    assert rendered.read_bytes() == module_path.read_bytes(), (
        f"{module_path.relative_to(REPO_ROOT)} differs from a fresh render. "
        "Run `python generate.py render` and commit the result, or fix the generator."
    )


def test_render_check_agrees_with_the_committed_tree():
    """`generate.py render --check` is green on a clean tree."""
    assert generate.render(check=True) == 0


def test_render_is_idempotent(tmp_path):
    """A second render over the same tree changes nothing."""
    first = {path: rendered.read_bytes() for path, rendered in generate.write_modules(tmp_path).items()}
    second = {path: rendered.read_bytes() for path, rendered in generate.write_modules(tmp_path).items()}
    assert first == second


@pytest.mark.parametrize("module_path", GENERATED_MODULES, ids=lambda p: p.name)
def test_generated_modules_do_not_import_legacy_paths(module_path):
    """The generated modules import aixplain.v1.* rather than leaning on _compat.py."""
    source = module_path.read_text(encoding="utf-8")
    assert not re.search(r"^from aixplain\.(base|enums|modules)\b", source, re.M)
    assert not re.search(r"^import aixplain\.(base|enums|modules)\b", source, re.M)


def test_injected_backend_values_render_to_valid_python(tmp_path, monkeypatch):
    """A hostile supplier name and function description parse as ordinary string data."""
    sentinel = tmp_path / "pwned"
    dataset = _synthetic_dataset(INJECTION_PAYLOAD.format(sentinel=sentinel))
    rendered = _render_synthetic(tmp_path, monkeypatch, dataset)

    for path in rendered.values():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert tree.body, f"{path} rendered empty"

    enums_source = rendered[generate.ENUMS_MODULE_PATH].read_text(encoding="utf-8")
    assert "os.system" in enums_source, "the payload should be present, as data"
    assert "import os" not in _executable_statements(enums_source), "the payload became executable code"


def test_injected_backend_values_are_inert_when_imported(tmp_path, monkeypatch):
    """Importing the rendered enum module runs none of the injected payload."""
    sentinel = tmp_path / "pwned"
    dataset = _synthetic_dataset(INJECTION_PAYLOAD.format(sentinel=sentinel))
    rendered = _render_synthetic(tmp_path, monkeypatch, dataset)
    enums_module = rendered[generate.ENUMS_MODULE_PATH]

    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT), AIXPLAIN_SUPPRESS_V1_DEPRECATION="1")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import runpy; ns = runpy.run_path({str(enums_module)!r}); print(ns['Supplier'].HOSTILE_SUPPLIER)",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    assert not sentinel.exists(), "the injected payload executed"
    assert "import os" in result.stdout, "the payload should survive as inert data"


@pytest.mark.parametrize(
    "function_id",
    ["3d-scan", "3.5-turbo", "!!!", "class", "café"],
    ids=["leading-digit", "version-number", "punctuation-only", "python-keyword", "non-ascii"],
)
def test_unusable_identifiers_fail_the_render(tmp_path, monkeypatch, function_id):
    """A backend value that cannot be an identifier fails loudly instead of being mangled."""
    dataset = _synthetic_dataset()
    dataset["functions"][0]["id"] = function_id

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    assert function_id in str(excinfo.value)


def test_colliding_enum_members_fail_the_render(tmp_path, monkeypatch):
    """Two values slugifying to the same member name fail here, not at user import time."""
    dataset = _synthetic_dataset()
    dataset["suppliers"].append({"id": 3, "name": "Hostile Supplier", "code": "hostile_supplier"})

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    message = str(excinfo.value)
    assert "hostile-supplier" in message and "hostile_supplier" in message


def test_identifier_validation_strips_whitespace_only():
    """Surrounding whitespace is trimmed; anything else is rejected."""
    assert generate.py_identifier("text ", source="test") == "text"
    with pytest.raises(generate.GeneratorValueError):
        generate.py_identifier("te xt", source="test")


def test_py_literal_preserves_non_ascii():
    """Literals keep the curly quotes already present in the committed output."""
    assert "“topics”" in generate.py_literal("the abstract “topics” that occur")


def test_render_makes_no_network_call(tmp_path, monkeypatch):
    """The render path never reaches the backend, so CI needs no credential."""

    def explode(*args, **kwargs):
        raise AssertionError("render must not touch the network")

    monkeypatch.setattr(generate.requests, "get", explode)
    monkeypatch.setattr(generate.requests, "post", explode, raising=False)

    written = generate.write_modules(tmp_path)
    assert all(path.exists() for path in written.values())


def test_render_runs_without_credentials(tmp_path):
    """`python generate.py` completes with every credential env var unset."""
    env = {k: v for k, v in os.environ.items() if k not in {"TEAM_API_KEY", "AIXPLAIN_API_KEY", "BACKEND_URL"}}
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "generate.py"), "render", "--check"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stderr


@pytest.fixture
def fetch_env(tmp_path, monkeypatch):
    """A fetch environment with one key, no `.env` on disk and a scratch fixture directory.

    Returns:
        Path: The scratch fixture directory.
    """
    monkeypatch.delenv("TEAM_API_KEY", raising=False)
    monkeypatch.delenv("AIXPLAIN_ALLOW_INSECURE_URLS", raising=False)
    monkeypatch.delenv("BACKEND_URL", raising=False)
    monkeypatch.setenv("AIXPLAIN_API_KEY", "a-key")
    monkeypatch.setattr(generate, "DOTENV_PATH", tmp_path / "absent.env")
    monkeypatch.setattr(generate, "FIXTURE_DIR", tmp_path / "fixtures")
    return tmp_path / "fixtures"


def test_fetch_requires_a_credential(fetch_env, monkeypatch):
    """The fetch step names both accepted env vars when neither is set."""
    monkeypatch.delenv("AIXPLAIN_API_KEY")

    with pytest.raises(ValueError, match="AIXPLAIN_API_KEY"):
        generate.resolve_fetch_config()


@pytest.mark.parametrize("env_var", ["TEAM_API_KEY", "AIXPLAIN_API_KEY"])
def test_fetch_accepts_either_api_key_env_var(monkeypatch, env_var):
    """Both documented key names are honoured (AGENTS.md)."""
    monkeypatch.delenv("TEAM_API_KEY", raising=False)
    monkeypatch.delenv("AIXPLAIN_API_KEY", raising=False)
    monkeypatch.setenv(env_var, "a-key")

    assert generate.get_config()["api_key"] == "a-key"


def test_default_backend_url_is_not_the_legacy_host(monkeypatch):
    """The legacy api.aixplain.com default is gone; the repo default is production."""
    monkeypatch.delenv("BACKEND_URL", raising=False)
    assert generate.get_config()["backend_url"] == "https://platform-api.aixplain.com"


def test_ruff_pin_matches_pre_commit():
    """The formatter is pinned identically in both places.

    The render step shells out to `ruff format`, so an unpinned ruff would turn a
    formatter release into a red drift job on an unrelated PR.
    """
    with open(PYPROJECT, "rb") as f:
        pyproject = tomllib.load(f)
    test_extra = pyproject["project"]["optional-dependencies"]["test"]
    pinned = [dep for dep in test_extra if dep.startswith("ruff==")]
    assert len(pinned) == 1, "the `test` extra must pin exactly one ruff version"
    version = pinned[0].split("==", 1)[1]

    config = PRE_COMMIT_CONFIG.read_text(encoding="utf-8")
    revs = re.findall(r"repo: https://github\.com/astral-sh/ruff-pre-commit\n\s*rev: v(\S+)", config)
    assert revs == [version], f"pyproject pins ruff {version}, .pre-commit-config.yaml pins {revs}"

    # The pytest-check hook builds its own env, so tests/unit/test_generator.py only
    # gets a formatter if the hook declares one -- at the same version.
    hook_pins = re.findall(r"^\s*- ruff==(\S+)$", config, re.M)
    assert hook_pins == [version], f"pyproject pins ruff {version}, the pytest-check hook pins {hook_pins}"


def _docstrings(source: str) -> dict:
    """Collect every class and function docstring in rendered source, wrap breaks removed.

    Args:
        source (str): Rendered module source.

    Returns:
        dict: Qualified name to docstring with every newline-plus-indent collapsed.
    """
    found = {}
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            found[node.name] = re.sub(r"\n\s*", "", ast.get_docstring(node) or "")
    return found


def test_long_token_with_backslashes_wraps_to_valid_python(tmp_path, monkeypatch):
    """A backslash straddling the wrap column is never split into a continuation plus a fresh escape."""
    description = "a" * 78 + "\\Users\\bob"
    dataset = _synthetic_dataset()
    dataset["functions"][0]["metaData"]["description"] = description
    rendered = _render_synthetic(tmp_path, monkeypatch, dataset)

    docstrings = _docstrings(rendered[generate.PIPELINE_MODULE_PATH].read_text(encoding="utf-8"))
    assert description in docstrings["TextGeneration"]
    assert description in docstrings["text_generation"]


def test_docstring_escapes_after_wrapping():
    """The escape is applied per wrapped line, so a unicode escape cannot be produced across a break."""
    text = "a" * 78 + "\\Users\\bob"
    rendered = generate.py_docstring(text)
    module = ast.parse(f'"""{rendered}"""')
    assert re.sub(r"\n\s*", "", module.body[0].value.value) == text


def test_padded_function_id_renders_stripped_identifiers(tmp_path, monkeypatch):
    """A whitespace-padded function id becomes a clean class, method and enum member name."""
    dataset = _synthetic_dataset()
    dataset["functions"][0]["id"] = "text-generation "
    rendered = _render_synthetic(tmp_path, monkeypatch, dataset)

    source = rendered[generate.PIPELINE_MODULE_PATH].read_text(encoding="utf-8")
    tree = ast.parse(source)
    classes = {n.name for n in tree.body if isinstance(n, ast.ClassDef)}
    assert {"TextGenerationInputs", "TextGenerationOutputs", "TextGeneration"} <= classes
    pipeline = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Pipeline")
    assert "text_generation" in {n.name for n in pipeline.body if isinstance(n, ast.FunctionDef)}
    assert 'function: str = "text-generation "' in source, "the wire-level id is emitted raw"

    enums = rendered[generate.ENUMS_MODULE_PATH].read_text(encoding="utf-8")
    assert 'TEXT_GENERATION = "text-generation "' in enums, "the enum member is stripped, the value raw"
    assert "TEXT_GENERATION_ " not in enums and "TEXT_GENERATION_ =" not in enums


def test_enumify_strips_before_slugifying():
    """Padding never becomes a trailing underscore, so a padded and a clean value are the same member."""
    assert generate.enumify("google ") == "GOOGLE"
    assert generate.enumify(" google") == "GOOGLE"
    assert generate.enumify("google") == generate.enumify("google ")


def test_padded_and_unpadded_supplier_codes_collide(tmp_path, monkeypatch):
    """`google` and `google ` are one member name, so the pair fails the render instead of shipping two."""
    dataset = _synthetic_dataset()
    dataset["suppliers"].append({"id": 3, "name": "Google", "code": "google"})
    dataset["suppliers"].append({"id": 4, "name": "Google", "code": "google "})

    with pytest.raises(generate.GeneratorValueError, match="Supplier.GOOGLE would be defined twice"):
        _render_synthetic(tmp_path, monkeypatch, dataset)


def test_padded_parameter_code_agrees_across_modules(tmp_path, monkeypatch):
    """The attribute is the stripped name; the wire-level `code=` is the raw backend code, in both modules."""
    dataset = _synthetic_dataset()
    dataset["functions"][0]["params"][0]["code"] = "text "
    dataset["functions"][0]["output"][0]["code"] = "data "
    rendered = _render_synthetic(tmp_path, monkeypatch, dataset)

    pipeline = rendered[generate.PIPELINE_MODULE_PATH].read_text(encoding="utf-8")
    assert 'self.text = self.create_param(code="text ", data_type=DataType.TEXT, is_required=True)' in pipeline
    assert 'self.data = self.create_param(code="data ", data_type=DataType.TEXT)' in pipeline

    enums = rendered[generate.ENUMS_MODULE_PATH].read_text(encoding="utf-8")
    assert '"code": "text "' in enums
    assert '"code": "data "' in enums


def test_known_duplicate_parameter_is_kept_once_in_both_modules(tmp_path, monkeypatch):
    """`benchmark-scoring-mt` serves `text` twice; both modules keep exactly one copy."""
    rendered = _render_synthetic(tmp_path, monkeypatch, _synthetic_dataset())

    pipeline = rendered[generate.PIPELINE_MODULE_PATH].read_text(encoding="utf-8")
    inputs = re.search(r"class BenchmarkScoringMtInputs\(Inputs\):(.*?)\n\n\nclass ", pipeline, re.S).group(1)
    assert inputs.count("self.create_param(") == 1

    enums = rendered[generate.ENUMS_MODULE_PATH].read_text(encoding="utf-8")
    spec = re.search(r'"benchmark-scoring-mt": \{(.*?)\n    \},', enums, re.S).group(1)
    assert spec.count('"code": "text"') == 1


def test_unlisted_duplicate_parameter_fails_the_render(tmp_path, monkeypatch):
    """A duplicate code on a function not in KNOWN_DUPLICATE_PARAMETERS fails, naming both copies."""
    dataset = _synthetic_dataset()
    dataset["functions"][0]["params"].append(
        {"code": "text ", "name": "reference", "dataType": "text", "required": True, "defaultValues": None}
    )

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    message = str(excinfo.value)
    assert "text-generation" in message and "'text '" in message and "'reference'" in message
    assert "KNOWN_DUPLICATE_PARAMETERS" in message


def test_known_duplicate_with_differing_copies_fails_the_render(tmp_path, monkeypatch):
    """The override only covers copies that agree on every emitted field."""
    dataset = _synthetic_dataset()
    metric = next(f for f in dataset["functions"] if f["id"] == "benchmark-scoring-mt")
    metric["params"][1]["required"] = False

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    assert "benchmark-scoring-mt" in str(excinfo.value) and "'required'" in str(excinfo.value)


def test_failed_formatting_leaves_the_target_files_untouched(tmp_path, monkeypatch):
    """A ruff failure never leaves raw or broken output where the tracked modules live."""
    target = tmp_path / "out"
    existing = target / generate.ENUMS_MODULE_PATH.relative_to(REPO_ROOT)
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"# committed content\n")

    def fail(paths):
        raise generate.GeneratorValueError("ruff is not installed")

    monkeypatch.setattr(generate, "ruff_format", fail)
    with pytest.raises(generate.GeneratorValueError, match="ruff is not installed"):
        generate.write_modules(target)

    assert existing.read_bytes() == b"# committed content\n"
    assert not (target / generate.PIPELINE_MODULE_PATH.relative_to(REPO_ROOT)).exists()
    assert not (target / generate.ENUMS_INCLUDE_PATH.relative_to(REPO_ROOT)).exists()


def test_null_description_renders_as_an_empty_string(tmp_path, monkeypatch):
    """`FunctionInputOutput[...]["spec"]["description"]` is `""` for a null description, as it always was."""
    dataset = _synthetic_dataset()
    dataset["functions"][0]["metaData"]["description"] = None
    rendered = _render_synthetic(tmp_path, monkeypatch, dataset)

    enums = rendered[generate.ENUMS_MODULE_PATH].read_text(encoding="utf-8")
    spec = re.search(r'"text-generation": \{(.*?)\n    \},', enums, re.S).group(1)
    assert '"description": ""' in spec
    assert '"description": None' not in enums


@pytest.mark.parametrize(
    ("family", "index", "field", "expected"),
    [
        ("suppliers", 1, "id", "suppliers.json[1] ('hostile-supplier') is missing 'id'"),
        ("licenses", 0, "id", "licenses.json[0] ('MIT') is missing 'id'"),
    ],
)
def test_missing_required_field_names_the_field_and_record(tmp_path, monkeypatch, family, index, field, expected):
    """A missing id fails with the field and record named, not Jinja's `Undefined`."""
    dataset = _synthetic_dataset()
    del dataset[family][index][field]

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    assert expected in str(excinfo.value)


def test_non_finite_floats_have_no_literal():
    """`repr(nan)` is a bare name that raises NameError at import, so it is refused."""
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(generate.GeneratorValueError, match="Non-finite"):
            generate.py_literal(value)
        with pytest.raises(generate.GeneratorValueError, match="Non-finite"):
            generate.py_literal({"defaultValues": [value]})
    assert generate.py_literal(1.5) == "1.5"


def test_fixture_with_non_finite_number_fails_to_load(tmp_path, monkeypatch):
    """`json` accepts NaN by default; the fixture loader does not."""
    dataset = _synthetic_dataset()
    _write_fixtures(tmp_path / "fixtures", dataset)
    functions = tmp_path / "fixtures" / "functions.json"
    functions.write_text(functions.read_text(encoding="utf-8").replace('"required": true', '"required": NaN', 1))
    monkeypatch.setattr(generate, "FIXTURE_DIR", tmp_path / "fixtures")

    with pytest.raises(generate.GeneratorValueError, match="non-finite number NaN"):
        generate.load_fixture("functions")


def _fake_get(calls):
    """Build a `requests.get` stand-in that records its keyword arguments.

    Args:
        calls (list): Receives one `(url, kwargs)` tuple per call.

    Returns:
        callable: The stand-in.
    """

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return _Response()

    return get


def test_fetch_passes_a_timeout(monkeypatch):
    """The catalog request cannot hang `fetch` forever, and sends exactly what it was given."""
    calls = []
    monkeypatch.setattr(generate.requests, "get", _fake_get(calls))

    generate.api_request("suppliers", "a-key", "https://platform-api.aixplain.com")

    assert calls == [
        (
            "https://platform-api.aixplain.com/sdk/suppliers",
            {"headers": {"Content-Type": "application/json", "x-api-key": "a-key"}, "timeout": (10, 30)},
        )
    ]


def test_fetch_refuses_a_plain_http_backend(fetch_env, monkeypatch):
    """`BACKEND_URL` goes through the SDK's URL policy, so the key is never sent in clear."""
    monkeypatch.setenv("BACKEND_URL", "http://platform-api.aixplain.com")
    calls = []
    monkeypatch.setattr(generate.requests, "get", _fake_get(calls))

    with pytest.raises(ValueError, match="BACKEND_URL must use https"):
        generate.fetch()

    assert calls == []


def _stub_api_request(monkeypatch, responses=None):
    """Replace `api_request` with a stand-in that records the endpoints asked for.

    Args:
        monkeypatch: pytest monkeypatch fixture.
        responses (dict, optional): Endpoint name to payload, or to an exception to raise.

    Returns:
        list: Receives one `(path, api_key, backend_url)` tuple per call.
    """
    calls = []

    def api_request(path, api_key, backend_url):
        calls.append((path, api_key, backend_url))
        response = (responses or {}).get(path, [])
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(generate, "api_request", api_request)
    return calls


def test_fetch_loads_only_the_repo_dotenv(fetch_env, monkeypatch):
    """`fetch` loads an explicit `.env` path (no parent walk-up)."""
    import dotenv

    loads = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path=None, **kwargs: loads.append((path, kwargs)) or False)
    _stub_api_request(monkeypatch)

    generate.fetch()

    assert loads == [(generate.DOTENV_PATH, {"override": False})]
    assert _load_generator().DOTENV_PATH == REPO_ROOT / ".env", "the default is the repo-root .env"


def test_fetch_refuses_a_non_production_host(fetch_env, monkeypatch, capsys):
    """A dev or test `BACKEND_URL` is refused before any request, so dev ids cannot reach the fixtures."""
    monkeypatch.setenv("BACKEND_URL", "https://dev-platform-api.aixplain.com")
    calls = _stub_api_request(monkeypatch)

    with pytest.raises(ValueError, match="not the production backend.*--allow-nonprod"):
        generate.fetch()

    assert calls == []
    assert not fetch_env.exists()


def test_fetch_from_a_non_production_host_needs_the_flag_and_is_recorded(fetch_env, monkeypatch, capsys):
    """`--allow-nonprod` captures anyway, warns, and writes the host into the provenance file."""
    monkeypatch.setenv("BACKEND_URL", "https://dev-platform-api.aixplain.com")
    calls = _stub_api_request(monkeypatch)

    generate.fetch(allow_nonprod=True)

    out = capsys.readouterr().out
    assert "Fetching from https://dev-platform-api.aixplain.com" in out
    assert "WARNING" in out and "not the production backend" in out
    assert {backend_url for _, _, backend_url in calls} == {"https://dev-platform-api.aixplain.com"}
    provenance = json.loads((fetch_env / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["backend_url"] == "https://dev-platform-api.aixplain.com"


def test_fetch_from_production_does_not_warn_and_records_provenance(fetch_env, monkeypatch, capsys):
    """The production host is the documented source of the committed fixtures."""
    calls = _stub_api_request(monkeypatch, {"suppliers": [{"id": 1769, "name": "Google", "code": "google"}]})

    generate.fetch()

    out = capsys.readouterr().out
    assert "Fetching from https://platform-api.aixplain.com" in out
    assert "WARNING" not in out
    assert [path for path, _, _ in calls] == list(generate.ENDPOINTS)
    assert {key for _, key, _ in calls} == {"a-key"}

    provenance = json.loads((fetch_env / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["backend_url"] == "https://platform-api.aixplain.com"
    assert datetime.fromisoformat(provenance["captured_at"]).tzinfo is not None
    assert provenance["fixtures"] == {
        name: hashlib.sha256((fetch_env / f"{name}.json").read_bytes()).hexdigest() for name in generate.ENDPOINTS
    }


def test_committed_fixtures_are_provenanced_from_production():
    """The committed snapshot names production and the digests match the committed files.

    Supplier ids are environment-specific (`google` is 1769 on production, 195 on dev, 212 on
    test), so a fixture from the wrong host would rewrite every `Supplier.*.value["id"]` in the
    shipped SDK; the digests make the provenance file describe these exact bytes.
    """
    provenance = json.loads(generate.provenance_path().read_text(encoding="utf-8"))
    assert urlparse(provenance["backend_url"]).hostname == "platform-api.aixplain.com"
    assert provenance["fixtures"] == {
        name: hashlib.sha256(generate.fixture_path(name).read_bytes()).hexdigest() for name in generate.ENDPOINTS
    }
    google = next(s for s in generate.load_fixture("suppliers") if s["code"] == "google")
    assert google["id"] == 1769


def test_main_wires_allow_nonprod_to_fetch(monkeypatch):
    """The CLI flag reaches `fetch`, and is off by default."""
    seen = []
    monkeypatch.setattr(generate, "fetch", lambda allow_nonprod: seen.append(allow_nonprod))

    assert generate.main(["fetch"]) == 0
    assert generate.main(["fetch", "--allow-nonprod"]) == 0
    assert seen == [False, True]


def test_failed_fetch_leaves_every_fixture_untouched(fetch_env, monkeypatch):
    """A failure on a later endpoint writes nothing, so a render cannot mix two catalog states."""
    committed = {name: f'[{{"{key}": "old-{name}"}}]\n'.encode() for name, key in generate.ENDPOINTS.items()}
    fetch_env.mkdir()
    for name, content in committed.items():
        (fetch_env / f"{name}.json").write_bytes(content)
    responses = {"languages": RuntimeError("403 Forbidden")}
    calls = _stub_api_request(monkeypatch, responses)

    with pytest.raises(RuntimeError, match="403"):
        generate.fetch()

    assert [path for path, _, _ in calls] == ["functions", "suppliers", "languages"]
    assert {name: (fetch_env / f"{name}.json").read_bytes() for name in committed} == committed
    assert not (fetch_env / "provenance.json").exists()


def test_fetch_uses_the_host_it_prints_even_with_a_cwd_dotenv(tmp_path):
    """The banner and the requests agree when a working-directory `.env` sets the host.

    `import aixplain` loads the CWD `.env`; resolving the config before that import and
    again after it made the banner say production while every request went to dev.
    """
    (tmp_path / ".env").write_text(
        "BACKEND_URL=https://dev-platform-api.aixplain.com\nAIXPLAIN_API_KEY=dotenv-key\n", encoding="utf-8"
    )
    script = textwrap.dedent(
        f"""
        import importlib.util, json
        from pathlib import Path
        spec = importlib.util.spec_from_file_location("aixplain_generate", {str(REPO_ROOT / "generate.py")!r})
        generate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generate)

        calls = []

        class Response:
            def raise_for_status(self):
                return None

            def json(self):
                return []

        generate.requests.get = lambda url, **kwargs: calls.append([url, kwargs["headers"]["x-api-key"]]) or Response()
        generate.DOTENV_PATH = Path({str(tmp_path / "absent.env")!r})
        generate.FIXTURE_DIR = Path({str(tmp_path / "fixtures")!r})
        generate.fetch(allow_nonprod=True)
        print("CALLS " + json.dumps(calls))
        """
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {"TEAM_API_KEY", "AIXPLAIN_API_KEY", "BACKEND_URL", "AIXPLAIN_ALLOW_INSECURE_URLS"}
    }
    env.update(PYTHONPATH=str(REPO_ROOT), AIXPLAIN_SUPPRESS_V1_DEPRECATION="1")
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    printed = re.search(r"^Fetching from (\S+)$", result.stdout, re.M).group(1)
    calls = json.loads(result.stdout.split("CALLS ", 1)[1])
    assert printed == "https://dev-platform-api.aixplain.com", "the CWD .env did not take effect"
    assert {url.split("/sdk/")[0] for url, _ in calls} == {printed}
    assert {key for _, key in calls} == {"dotenv-key"}


def test_team_api_key_takes_precedence_like_the_sdk(monkeypatch):
    """Precedence mirrors `aixplain.v2.core.Aixplain`: TEAM_API_KEY first."""
    monkeypatch.setenv("TEAM_API_KEY", "same-key")
    monkeypatch.setenv("AIXPLAIN_API_KEY", "same-key")
    assert generate.get_config()["api_key"] == "same-key"

    monkeypatch.delenv("AIXPLAIN_API_KEY")
    assert generate.get_config()["api_key"] == "same-key"


def test_conflicting_api_keys_are_refused(monkeypatch):
    """Two different keys are refused rather than one being silently picked."""
    monkeypatch.setenv("TEAM_API_KEY", "team-key")
    monkeypatch.setenv("AIXPLAIN_API_KEY", "other-key")

    with pytest.raises(ValueError, match="TEAM_API_KEY and AIXPLAIN_API_KEY are both set and differ"):
        generate.get_config()


def test_data_types_agree_with_the_sdk_enum():
    """The frozen set the render validates against is exactly `aixplain.v1.enums.DataType`.

    The render path cannot import the package it generates, so the values are copied;
    this is what keeps the copy honest when a member is added to the enum.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # the v1 deprecation notice, on first import
        from aixplain.v1.enums.data_type import DataType

    assert generate.DATA_TYPES == {member.value for member in DataType}
    assert all(DataType(value).name == value.upper() for value in generate.DATA_TYPES), (
        "the pipeline template emits DataType.<VALUE.upper()>"
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda f: f["params"][0].__setitem__("dataType", "hologram"),
        lambda f: f["output"][0].__setitem__("dataType", "hologram"),
        lambda f: f["metaData"].__setitem__("InputType", "hologram"),
        lambda f: f["metaData"].__setitem__("OutputType", "hologram"),
    ],
    ids=["param", "output", "InputType", "OutputType"],
)
def test_unknown_data_type_fails_the_render(tmp_path, monkeypatch, mutate):
    """A type outside `DataType` fails here, not as an AttributeError in `import aixplain.v1.modules`."""
    dataset = _synthetic_dataset()
    mutate(dataset["functions"][0])

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    message = str(excinfo.value)
    assert "'hologram'" in message and "text-generation" in message and "DataType" in message


def test_rendered_pipeline_module_executes(tmp_path, monkeypatch):
    """The rendered `pipeline.py` imports against the real package and resolves every `DataType`."""
    rendered = _render_synthetic(tmp_path, monkeypatch, _synthetic_dataset())
    pipeline_module = rendered[generate.PIPELINE_MODULE_PATH]

    script = textwrap.dedent(
        f"""
        import importlib.util
        import aixplain.v1.modules.pipeline  # the real package, so the relative imports resolve
        from aixplain.v1.enums import DataType

        spec = importlib.util.spec_from_file_location("aixplain.v1.modules.pipeline.pipeline", {str(pipeline_module)!r})
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.TextGeneration.input_type is DataType.TEXT
        assert module.BenchmarkScoringAsr.input_type is DataType.AUDIO
        assert module.BenchmarkScoringMt.output_type is DataType.LABEL, "the padded OutputType"
        inputs = module.BenchmarkScoringMtInputs()
        assert inputs.text.data_type is DataType.TEXT
        assert issubclass(module.Pipeline, aixplain.v1.modules.pipeline.pipeline.DefaultPipeline)
        print("ok")
        """
    )
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT), AIXPLAIN_SUPPRESS_V1_DEPRECATION="1")
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


@pytest.mark.parametrize("char", ["\x00", "\x1b", "\u200b"], ids=["nul", "escape", "zero-width-space"])
def test_control_character_in_description_fails_the_render(tmp_path, monkeypatch, char):
    """A control character in a docstring survives escaping, so it is refused with the function named."""
    dataset = _synthetic_dataset()
    dataset["functions"][0]["metaData"]["description"] = f"Generates{char}text."

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    message = str(excinfo.value)
    assert "text-generation" in message and repr(char) in message and "docstring" in message


def test_description_ending_in_quotes_round_trips(tmp_path, monkeypatch):
    """A description ending in `\"\"\"` or `"` is neither a SyntaxError nor double-escaped."""
    dataset = _synthetic_dataset()
    dataset["functions"][0]["metaData"]["description"] = 'Ends in triple """'
    dataset["functions"][1]["metaData"]["description"] = 'Ends in one "'
    rendered = _render_synthetic(tmp_path, monkeypatch, dataset)

    docstrings = _docstrings(rendered[generate.PIPELINE_MODULE_PATH].read_text(encoding="utf-8"))
    assert 'node.Ends in triple """InputType' in docstrings["TextGeneration"]
    assert docstrings["text_generation"].endswith('node.Ends in triple """')
    assert 'node.Ends in one "InputType' in docstrings["SplitOnLinebreak"]
    assert docstrings["split_on_linebreak"].endswith('node.Ends in one "')


def _crlf_open(file, mode="r", buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    """`open` as Windows behaves: a text-mode write with no `newline=` translates LF to CRLF."""
    if "b" not in mode and newline is None and set(mode) & set("wax"):
        newline = "\r\n"
    return _real_open(file, mode, buffering, encoding, errors, newline, closefd, opener)


_real_open = builtins.open


def test_written_files_are_lf_even_where_the_platform_default_is_crlf(tmp_path, monkeypatch, fetch_env):
    """Staged renders and fixtures are written with explicit LF, so a Windows render matches the committed bytes."""
    _write_fixtures(tmp_path / "fixtures", _synthetic_dataset())
    _stub_api_request(monkeypatch, {"suppliers": [{"id": 1, "name": "aixplain", "code": "aixplain"}]})

    with monkeypatch.context() as context:
        # `builtins.open` is what generate.py calls; `io.open` is what pathlib calls.
        context.setattr(builtins, "open", _crlf_open)
        context.setattr(io, "open", _crlf_open)
        assert (tmp_path / "probe.txt").write_text("a\n") and b"\r\n" in (tmp_path / "probe.txt").read_bytes(), (
            "the emulation must actually produce CRLF, or this test proves nothing"
        )
        written = generate.write_modules(tmp_path / "out")
        generate.fetch()

    for path in written.values():
        assert b"\r" not in path.read_bytes(), f"{path.name} was written with CRLF"
    for path in fetch_env.iterdir():
        assert b"\r" not in path.read_bytes(), f"{path.name} was written with CRLF"


def test_duplicate_output_code_fails_even_for_an_allow_listed_function(tmp_path, monkeypatch):
    """The allow-list covers inputs only; a duplicated output code always fails."""
    dataset = _synthetic_dataset()
    metric = next(f for f in dataset["functions"] if f["id"] == "benchmark-scoring-mt")
    metric["output"].append({"code": "data", "dataType": "label", "defaultValue": None})

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    assert "outputs of functions.json" in str(excinfo.value) and "benchmark-scoring-mt" in str(excinfo.value)


def test_known_duplicate_with_unexpected_names_fails_the_render(tmp_path, monkeypatch):
    """The entry pins the names of the pair it was written for; a different pair fails."""
    dataset = _synthetic_dataset()
    metric = next(f for f in dataset["functions"] if f["id"] == "benchmark-scoring-mt")
    metric["params"][1]["name"] = "hypothesis"

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    message = str(excinfo.value)
    assert "('output', 'reference')" in message and "('output', 'hypothesis')" in message


def test_stale_known_duplicate_entry_fails_the_render(tmp_path, monkeypatch):
    """An entry the catalog no longer exercises fails, so the special case cannot outlive its data."""
    dataset = _synthetic_dataset()
    metric = next(f for f in dataset["functions"] if f["id"] == "benchmark-scoring-mt")
    del metric["params"][1]

    with pytest.raises(generate.GeneratorValueError) as excinfo:
        _render_synthetic(tmp_path, monkeypatch, dataset)

    message = str(excinfo.value)
    assert "benchmark-scoring-mt" in message and "'text'" in message and "no longer serves it twice" in message


def test_known_duplicate_for_a_missing_function_fails_the_render(tmp_path, monkeypatch):
    """An entry for a function the catalog does not have fails too."""
    monkeypatch.setattr(
        generate,
        "KNOWN_DUPLICATE_PARAMETERS",
        {**generate.KNOWN_DUPLICATE_PARAMETERS, "benchmark-scoring-retired": {"text": ("output", "reference")}},
    )

    with pytest.raises(generate.GeneratorValueError, match="'benchmark-scoring-retired'.*no such function"):
        _render_synthetic(tmp_path, monkeypatch, _synthetic_dataset())
