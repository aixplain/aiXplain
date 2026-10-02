"""Functional tests for custom Python code — the surface ``aix.Utility`` became.

Custom code is a ``Tool`` in v2, run in the Python Sandbox integration, so this
covers the ``parse_code`` / ``_upload_code`` path end to end: author from raw
source and from a callable, run with typed inputs, update the source, run again,
delete. The module is named after the removed resource because
``MIGRATION.md``'s headline ``ScriptFactory`` / ``create_utility_model``
replacement had no end-to-end test.
"""

import time

import pytest

RAW_ADD = '''
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b
'''

RAW_MULTIPLY = '''
def add(a: int, b: int) -> int:
    """Add two integers, but multiplied (updated entrypoint)."""
    return (a + b) * 10
'''


def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


def _unique_name(prefix: str) -> str:
    return f"{prefix}-{int(time.time())}-{time.time_ns() % 100000}"


class TestCodeToolLifecycle:
    def test_create_from_raw_code_run_update_run_delete(self, client, resource_tracker):
        tool = client.Tool(
            name=_unique_name("func-utility-raw"),
            description="Add two integers.",
            code=RAW_ADD,
        )
        tool.save()
        resource_tracker.append(tool)

        fetched = client.Tool.get(tool.id)
        assert fetched.id == tool.id
        assert fetched.config is None or "function_name" in (fetched.config or {})

        first = tool.run(action="add", data={"a": 2, "b": 3})
        assert first.status == "SUCCESS", first
        assert first.completed is True

        tool.config = {"code": RAW_MULTIPLY, "function_name": "add"}
        tool.save()

        second = client.Tool.get(tool.id)
        updated = second.run(action="add", data={"a": 2, "b": 3})
        assert updated.status == "SUCCESS", updated
        assert updated.completed is True

    def test_create_from_callable(self, client, resource_tracker):
        tool = client.Tool(
            name=_unique_name("func-utility-callable"),
            description="Multiply two integers.",
            code=multiply,
        )
        tool.save()
        resource_tracker.append(tool)

        result = tool.run(action="multiply", data={"a": 6, "b": 7})
        assert result.status == "SUCCESS", result
        assert result.completed is True


class TestCodeToolRejectsInvalidCode:
    def test_code_without_a_function_is_rejected(self, client):
        with pytest.raises(ValueError, match="No function"):
            client.Tool(name=_unique_name("func-utility-invalid"), code="x = 1\n")

    def test_code_with_a_syntax_error_is_rejected(self, client):
        with pytest.raises(ValueError, match="not valid Python"):
            client.Tool(name=_unique_name("func-utility-syntax"), code="def main(:\n    return 1\n")

    def test_unknown_entrypoint_is_rejected(self, client):
        with pytest.raises(ValueError, match="not found in code"):
            client.Tool(
                name=_unique_name("func-utility-entry"),
                code="def main():\n    return 1\n",
                config={"function_name": "missing"},
            )
