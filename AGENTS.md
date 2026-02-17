# aiXplain SDK

Python SDK for building, deploying, and governing AI agents on the aiXplain platform.

- License: Apache 2.0
- Python: >=3.9, <4
- Package config: `pyproject.toml` (PEP 621, setuptools backend)

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

Set `AIXPLAIN_API_KEY` (required) before using the SDK. `BACKEND_URL` defaults to production (`https://platform-api.aixplain.com`).

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

Hooks run: trailing-whitespace, end-of-file-fixer, check-merge-conflict, check-added-large-files, ruff (lint + format), and unit tests.

---

## Coding Conventions

- **Line length**: 120 characters.
- **Indentation**: 4 spaces.
- **Quotes**: Double quotes for strings.
- **Docstrings**: Google style (enforced by ruff `pydocstyle`). Docstring rules are **not** enforced in `tests/`.
- **Type hints**: Required on all public functions. Use `typing` (`Optional`, `Union`, `List`, `Dict`, `TypeVar`, generics).
- **Naming**: `PascalCase` for classes, `snake_case` for functions and methods, `UPPER_SNAKE_CASE` for constants.
- **Exceptions**: Use the custom hierarchy in `aixplain/exceptions/` (`AixplainBaseException` and subclasses). Never raise bare `Exception`.
- **Imports**: Use `from __future__ import annotations` or `TYPE_CHECKING` guards to break circular imports. Use conditional imports for optional dependencies.
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
| `aixplain/modules/` | Domain objects (Agent, Model, Pipeline, TeamAgent, tools) |
| `aixplain/factories/` | V1 factory classes for creating and managing resources |
| `aixplain/v2/` | V2 resource classes with mixins and hook system |
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

## Testing

- **Framework**: pytest (configured in `pytest.ini`, `testpaths = tests`).
- **Unit tests**: `tests/unit/` -- fast, mocked, no network calls.
- **Functional tests**: `tests/functional/` -- integration tests against real or staged services.
- **Mock data**: `tests/mock_responses/` -- JSON fixtures for API responses.
- **CI**: GitHub Actions runs 16 parallel test suites (unit, agent, model, pipeline, v2, finetune, etc.) on Python 3.9 with a 45-minute timeout.
- **Docstrings in tests**: Not enforced (ruff ignores `D` rules for `tests/**/*.py`).

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
