# aiXplain SDK

Python SDK for building, deploying, and governing AI agents on the aiXplain platform.

- License: Apache 2.0
- Python: >=3.9, <4
- Package config: `pyproject.toml` (PEP 621, setuptools backend)

---

## Primary Goal

- Keep the SDK stable for existing users while improving the current `development` branch.
- `v2` is the only SDK surface. `v1` was removed in 0.3.0.

---

## Source of Truth

- Package metadata and dependencies live in `pyproject.toml`.
- Formatting and docstring rules live in `ruff.toml`.
- Pre-commit behavior lives in `.pre-commit-config.yaml`.
- CI behavior lives in `.github/workflows/`.
- Public package bootstrapping lives in `aixplain/__init__.py`; `aixplain/_compat.py` turns a removed v1 import into an error naming its v2 replacement.

If this file conflicts with code, tests, or CI, follow the code and tests and update this file in the same change when appropriate.

---

## Setup and Commands

```bash
# Install (development)
pip install -e .

# Install (production)
pip install aixplain

# Install with test dependencies
pip install -e ".[test]"
```

### Environment

The SDK supports either `TEAM_API_KEY` or `AIXPLAIN_API_KEY`. New code must not assume only one of those environment variables exists. `BACKEND_URL` defaults to production (`https://platform-api.aixplain.com`).

Additional environment variables for execution URLs:
- `MODELS_RUN_URL`
- `PIPELINES_RUN_URL`

In `v2`, prefer instance-scoped configuration through `Aixplain(...)` and its context rather than new global state.

### Test

```bash
# Unit tests
python -m pytest tests/unit

# Functional / integration tests
python -m pytest tests/functional

# Unit tests with coverage (same as pre-commit hook)
coverage run --source=. -m pytest tests/unit
```

### Lint and Format

Ruff is the sole linter and formatter.

```bash
ruff check .            # Lint
ruff check --fix .      # Lint with auto-fix
ruff format .           # Format
```

### Pre-commit

```bash
pre-commit install
```

Hooks run: trailing-whitespace, end-of-file-fixer, check-merge-conflict, check-added-large-files, ruff (lint + format for `aixplain/v2/`), and unit tests with coverage.

---

## Coding Conventions

- **Line length**: 120 characters.
- **Indentation**: 4 spaces.
- **Quotes**: Double quotes for strings.
- **Docstrings**: Google style (enforced by ruff `pydocstyle`). Docstring rules are **not** enforced in `tests/`.
- **Type hints**: Required on all public functions. Use `typing` (`Optional`, `Union`, `List`, `Dict`, `TypeVar`, generics).
- **Naming**: `PascalCase` for classes, `snake_case` for functions and methods, `UPPER_SNAKE_CASE` for constants.
- **Exceptions**: Use the custom hierarchy in `aixplain/exceptions/` (`AixplainBaseException` and subclasses). Never raise bare `Exception`. Preserve useful context in error messages and include status or response details when available.
- **Imports**: Use `from __future__ import annotations` or `TYPE_CHECKING` guards to break circular imports. Use conditional imports for optional dependencies. Do not add a new dependency unless it is necessary and justified by the repository's existing design.
- **Validation**: Pydantic for runtime validation. `dataclasses-json` for JSON serialization.
- **License header**: Include the Apache 2.0 license header at the top of every source file.

---

## Architecture

### One API Surface

`aixplain/v2/` is the SDK. Resources hang off an `Aixplain(...)` client, are dataclasses composed
from mixins, and serialize through `dataclasses-json` (camelCase API to snake_case Python).

> **V1 was removed in 0.3.0** (`aixplain/v1/` and the `_compat.py` redirects). The last release
> that contained it is `0.2.48`, which stays installable. Both versions live in exactly one place,
> `aixplain._compat.V1_REMOVED_IN` and `aixplain._compat.LAST_V1_RELEASE`;
> `tests/unit/test_v1_removal.py` fails if any hand-written doc disagrees, so change the constants
> and then the docs, never the reverse. Importing a legacy path raises a `ModuleNotFoundError`
> naming the v2 replacement — see [`MIGRATION.md`](MIGRATION.md) for the factory-by-factory map,
> including the eight factories that had no v2 equivalent and were removed without one.

### Package Layout

| Directory | Purpose |
|---|---|
| `aixplain/v2/` | The SDK surface. All new features and fixes go here. |
| `aixplain/_compat.py` | Turns an import of a removed v1 path into an error naming its v2 replacement. Nothing is redirected. |
| `aixplain/exceptions/` | Custom exception hierarchy with error codes and categories |
| `aixplain/utils/` | Shared helpers (config, URL safety policy, run metadata) |

### Key Design Patterns

- **Mixin**: `SearchResourceMixin`, `GetResourceMixin`, `RunnableResourceMixin`, `ToolableMixin` for composable behavior (V2).
- **Hook**: `before_save` / `after_save` lifecycle hooks on resources (V2).
- **Builder**: `build_run_payload()` / `build_save_payload()` methods.
- **Strategy**: Sync, async, and streaming execution paths.
- **Run metadata**: agent run payloads carry a `metaData` object from `aixplain.utils.user_info_utils.build_run_metadata()` (one cached `ipinfo.io` lookup). If you change what it sends, update [docs/run-metadata.md](docs/run-metadata.md) — `tests/unit/test_run_metadata_docs.py` enforces it.

---

## Change Scope Rules

- Make the smallest change that fully solves the task.
- Do not do opportunistic refactors unless they are required to complete the requested work safely.
- Do not remove deprecated parameters or other compatibility paths unless the task explicitly requires a breaking change.

### V2 Rules

- Treat `aixplain/v2/` as the default surface for all new SDK behavior.
- Keep `v2` self-contained. The only `aixplain.utils` modules it may import are `url_safety` and `user_info_utils`.
- Internal Python identifiers in `v2` should be `snake_case`. Convert to the API's `camelCase` only at the network or serialization boundary.
- Prefer typed, explicit resource and client code over dynamic dict-heavy plumbing.
- Preserve the multi-instance pattern centered on `Aixplain(api_key=...)`.
- Do not add import-time behavior in `v2` that forces users onto a global env-var validation chain.
- Anything a caller has to construct or pass in accepts plain data (a dict typed as a `TypedDict`, or a
  string typed as a `Literal`) as well as the object, and an unknown key raises. Anything that only ever
  comes back from the SDK stays an object. Every `v2` enum and non-resource dataclass is classified in
  [docs/v2-plain-data.md](docs/v2-plain-data.md); add a row there when you add one.
- Everything importable is importable from `aixplain` directly. `aixplain/__init__.py` re-exports
  `aixplain.v2.__all__`, so a new public symbol needs only an entry in `aixplain/v2/__init__.py`.

---

## Testing

- **Framework**: pytest (configured in `pytest.ini`, `testpaths = tests`).
- **Unit tests**: `tests/unit/` -- fast, mocked, no network calls.
- **Functional tests**: `tests/functional/` -- integration tests against real or staged services.
- **Mock data**: `tests/mock_responses/` -- JSON fixtures for API responses.
- **CI**: GitHub Actions runs the credential-free unit suite plus one functional leg per `tests/functional/v2/test_*.py` file (`agent`, `model`, ...) on Python 3.9 with a 30-minute timeout each. A new functional test file needs its own leg in `.github/workflows/main.yaml`; `tests/unit/test_ci_matrix_coverage.py` fails otherwise.
- **Docstrings in tests**: Not enforced (ruff ignores `D` rules for `tests/**/*.py`).
- Prefer targeted unit tests under `tests/unit/v2/`.

---

## New Files

- New Python source files should include the repository's Apache 2.0 header format used in package modules.
- Place new files inside the existing package layout. Do not invent a new top-level package or directory for SDK code without explicit direction.

---

## Common Mistakes to Avoid

- Do not reintroduce `aixplain.modules` / `aixplain.factories` / `aixplain.enums` imports anywhere.
- Do not leak Python `snake_case` field names into API payloads that expect `camelCase`.
- Do not hardcode a single API-key env-var assumption.
- Do not edit generated docs or unrelated documentation unless the task requires it.

---

## Review Checklist

Before finishing, check the following:

- Did you preserve backward compatibility where expected?
- Did you keep internal names `snake_case` and API payload keys `camelCase` where required?
- Did you update or add focused tests?
- Did you avoid unrelated refactors?

---

## Domain Glossary

| Term | Description |
|---|---|
| **Agent** | An autonomous AI entity that reasons, plans, and uses tools to complete tasks. |
| **Model** | An AI model (LLM, utility, or index) accessible through the platform. |
| **Pipeline** | A sequential workflow connecting models and tools in a fixed order. |
| **TeamAgent** | A multi-agent system where multiple agents collaborate. |
| **Tool** | A capability an agent can invoke (model tool, pipeline tool, Python interpreter, SQL, etc.). |
| **Microagent** | Built-in specialized components: **Mentalist** (planning), **Orchestrator** (routing), **Inspector** (validation), **Bodyguard** (security), **Responder** (formatting). |
| **Meta-agent** | Agents that improve other agents. The **Evolver** monitors KPIs and refines behavior. |
| **Static orchestration** | Deterministic execution with predefined `AgentTask` ordering. |
| **Dynamic orchestration** | Adaptive execution where the Mentalist generates the plan at runtime (default). |
