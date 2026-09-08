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
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

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
                {"code": "text", "dataType": "text", "required": True},
                # The catalog does serve a duplicated parameter code; see ENG-3435.
                {"code": "text", "dataType": "text", "required": True},
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


def test_fetch_requires_a_credential(monkeypatch):
    """The fetch step names both accepted env vars when neither is set."""
    monkeypatch.delenv("TEAM_API_KEY", raising=False)
    monkeypatch.delenv("AIXPLAIN_API_KEY", raising=False)

    with pytest.raises(ValueError, match="AIXPLAIN_API_KEY"):
        generate.api_request("functions")


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
    """A whitespace-padded function id becomes a clean class and method name, not a SyntaxError."""
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
    """The catalog request cannot hang `fetch` forever."""
    monkeypatch.delenv("AIXPLAIN_API_KEY", raising=False)
    monkeypatch.delenv("AIXPLAIN_ALLOW_INSECURE_URLS", raising=False)
    monkeypatch.setenv("TEAM_API_KEY", "a-key")
    monkeypatch.setenv("BACKEND_URL", "https://platform-api.aixplain.com")
    calls = []
    monkeypatch.setattr(generate.requests, "get", _fake_get(calls))

    generate.api_request("suppliers")

    assert calls == [
        (
            "https://platform-api.aixplain.com/sdk/suppliers",
            {"headers": {"Content-Type": "application/json", "x-api-key": "a-key"}, "timeout": (10, 30)},
        )
    ]


def test_fetch_refuses_a_plain_http_backend(monkeypatch):
    """`BACKEND_URL` goes through the SDK's URL policy, so the key is never sent in clear."""
    monkeypatch.delenv("AIXPLAIN_API_KEY", raising=False)
    monkeypatch.delenv("AIXPLAIN_ALLOW_INSECURE_URLS", raising=False)
    monkeypatch.setenv("TEAM_API_KEY", "a-key")
    monkeypatch.setenv("BACKEND_URL", "http://platform-api.aixplain.com")
    calls = []
    monkeypatch.setattr(generate.requests, "get", _fake_get(calls))

    with pytest.raises(ValueError, match="BACKEND_URL must use https"):
        generate.api_request("suppliers")

    assert calls == []


def test_fetch_loads_only_the_repo_dotenv_and_prints_the_host(tmp_path, monkeypatch, capsys):
    """`fetch` loads an explicit `.env` path (no parent walk-up) and says which backend it captured."""
    import dotenv

    loads = []
    monkeypatch.setattr(dotenv, "load_dotenv", lambda path=None, **kwargs: loads.append((path, kwargs)) or False)
    monkeypatch.setattr(generate, "api_request", lambda name: [])
    monkeypatch.setattr(generate, "FIXTURE_DIR", tmp_path / "fixtures")
    monkeypatch.setenv("BACKEND_URL", "https://dev-platform-api.aixplain.com")

    generate.fetch()

    assert loads == [(REPO_ROOT / ".env", {"override": False})]
    out = capsys.readouterr().out
    assert "Fetching from https://dev-platform-api.aixplain.com" in out
    assert "WARNING" in out and "not the production backend" in out


def test_fetch_from_production_does_not_warn(tmp_path, monkeypatch, capsys):
    """The production host is the documented source of the committed fixtures."""
    import dotenv

    monkeypatch.setattr(dotenv, "load_dotenv", lambda path=None, **kwargs: False)
    monkeypatch.setattr(generate, "api_request", lambda name: [])
    monkeypatch.setattr(generate, "FIXTURE_DIR", tmp_path / "fixtures")
    monkeypatch.delenv("BACKEND_URL", raising=False)

    generate.fetch()

    out = capsys.readouterr().out
    assert "Fetching from https://platform-api.aixplain.com" in out
    assert "WARNING" not in out


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
