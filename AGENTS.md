# aiXplain SDK

Python SDK for building, deploying, and governing AI agents on the aiXplain platform.

- License: Apache 2.0
- Python: >=3.9, <4
- Package config: `pyproject.toml` (PEP 621, setuptools backend)

---

## Primary Goal

- Keep the SDK stable for existing users while improving the current `development` branch.
- Default to the `v2` SDK surface for new work.
- Preserve backward compatibility for the legacy `v1` surface and legacy import paths.

---

## Source of Truth

- Package metadata and dependencies live in `pyproject.toml`.
- Formatting and docstring rules live in `ruff.toml`.
- Pre-commit behavior lives in `.pre-commit-config.yaml`.
- CI behavior lives in `.github/workflows/`.
- Public package bootstrapping and legacy import compatibility live in `aixplain/__init__.py` and `aixplain/_compat.py`.

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

### Dual API Surface

The SDK exposes two API layers maintained in parallel:

| Aspect | V1 | V2 |
|---|---|---|
| Style | Factory pattern with class methods | Resource-based with dataclasses and mixins |
| Entry point | `aixplain.factories.*Factory` | `aixplain.v2.*` |
| Serialization | Manual dict handling | `dataclasses-json` (camelCase API to snake_case Python) |

### Package Layout

| Directory | Purpose |
|---|---|
| `aixplain/v2/` | Current SDK surface. Prefer this for new features and fixes unless the task is explicitly about legacy behavior. |
| `aixplain/v1/` | Legacy SDK implementation. Touch this for compatibility fixes, bug fixes, or explicitly requested v1 work. |
| `aixplain/_compat.py` | Legacy import redirector. Existing imports like `aixplain.modules` and `aixplain.factories` must continue to work. |
| `aixplain/modules/` | Domain objects (Agent, Model, Pipeline, TeamAgent, tools) |
| `aixplain/factories/` | V1 factory classes for creating and managing resources |
| `aixplain/enums/` | Enumerations (Function, Supplier, Language, Status, etc.) |
| `aixplain/exceptions/` | Custom exception hierarchy with error codes and categories |
| `aixplain/utils/` | Shared helpers (config, HTTP requests, file utilities, caching) |
| `aixplain/base/` | Base parameters |
| `aixplain/decorators/` | Decorators (e.g., API key checker) |
| `aixplain/processes/` | Data onboarding workflows |

### Key Design Patterns

- **Factory**: `AgentFactory`, `ModelFactory`, `PipelineFactory`, etc. for resource creation (V1).
- **Mixin**: `SearchResourceMixin`, `GetResourceMixin`, `RunnableResourceMixin`, `ToolableMixin` for composable behavior (V2).
- **Hook**: `before_save` / `after_save` lifecycle hooks on resources (V2).
- **Builder**: `build_run_payload()` / `build_save_payload()` methods.
- **Strategy**: Sync, async, and streaming execution paths.

---

## Change Scope Rules

- Make the smallest change that fully solves the task.
- Do not do opportunistic refactors unless they are required to complete the requested work safely.
- Do not silently move functionality between `v1` and `v2`.
- Do not remove compatibility paths, deprecated parameters, or legacy import routes unless the task explicitly requires a breaking change.

### V2 Rules

- Treat `aixplain/v2/` as the default surface for all new SDK behavior.
- Keep `v2` self-contained. Do not import from legacy paths such as `aixplain.modules`, `aixplain.factories`, `aixplain.enums`, or `aixplain.utils`.
- Internal Python identifiers in `v2` should be `snake_case`. Convert to the API's `camelCase` only at the network or serialization boundary.
- Prefer typed, explicit resource and client code over dynamic dict-heavy plumbing.
- Preserve the multi-instance pattern centered on `Aixplain(api_key=...)`.
- Do not add import-time behavior in `v2` that forces users onto the legacy env-var validation chain.

### V1 and Compatibility Rules

- Treat `aixplain/v1/` as a compatibility surface.
- For new capabilities, prefer adding them in `v2` unless the task explicitly asks for `v1`.
- When fixing `v1`, preserve current public behavior unless the bug fix requires a narrow, well-justified change.
- Keep legacy imports working through `aixplain/_compat.py`.
- Do not introduce changes in `v1` that break users importing from historical paths like `aixplain.modules.*` or `aixplain.factories.*`.

---

## Testing

- **Framework**: pytest (configured in `pytest.ini`, `testpaths = tests`).
- **Unit tests**: `tests/unit/` -- fast, mocked, no network calls.
- **Functional tests**: `tests/functional/` -- integration tests against real or staged services.
- **Mock data**: `tests/mock_responses/` -- JSON fixtures for API responses.
- **CI**: GitHub Actions runs parallel test suites (unit, agent, model, pipeline, v2, finetune, etc.) on Python 3.9 with a 45-minute timeout.
- **Docstrings in tests**: Not enforced (ruff ignores `D` rules for `tests/**/*.py`).
- For `v2` work, prefer targeted unit tests under `tests/unit/v2/`.
- For legacy work, add or update the narrowest relevant unit or functional tests.

---

## New Files

- New Python source files should include the repository's Apache 2.0 header format used in package modules.
- Place new files inside the existing package layout. Do not invent a new top-level package or directory for SDK code without explicit direction.

---

## Common Mistakes to Avoid

- Do not add `v1` imports inside `aixplain/v2/`.
- Do not leak Python `snake_case` field names into API payloads that expect `camelCase`.
- Do not break legacy import compatibility by bypassing or removing `_compat.py`.
- Do not hardcode a single API-key env-var assumption.
- Do not make `v2` depend on import-time side effects from legacy modules.
- Do not edit generated docs or unrelated documentation unless the task requires it.

---

## Review Checklist

Before finishing, check the following:

- Is the change in the correct surface, `v2` or `v1`?
- Did you preserve backward compatibility where expected?
- Did you avoid `v1` imports from `v2`?
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
