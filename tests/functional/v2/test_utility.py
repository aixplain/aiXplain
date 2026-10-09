"""Functional tests for custom Python code — the surface ``aix.Utility`` became.

Custom code is a ``Tool`` in v2: its source and entrypoint travel in the tool's
``config`` to the Python Sandbox integration, which runs them. This covers that
path end to end: author from raw source and from a callable, run with typed
inputs, update the source, run again, delete. (``code_utils.parse_code`` /
``_upload_code`` are not on this path; they are unit-tested in
``tests/unit/v2/test_code_utils.py``, as is the offline code validation.) The
module is named after the removed resource because ``MIGRATION.md``'s headline
``ScriptFactory`` / ``create_utility_model`` replacement had no end-to-end test.
"""

from tests.functional._helpers import unique_name

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


def _returned_value(result) -> str:
    """The entrypoint's return value as text, unwrapped from the sandbox's result envelope."""
    data = result.data
    if isinstance(data, dict):
        for key in ("output", "result", "data", "value"):
            if key in data:
                data = data[key]
                break
    return str(data).strip()


class TestCodeToolLifecycle:
    def test_create_from_raw_code_run_update_run_delete(self, client, resource_tracker):
        tool = client.Tool(
            name=unique_name("func-utility-raw"),
            description="Add two integers.",
            code=RAW_ADD,
        )
        tool.save()
        resource_tracker.append(tool)

        fetched = client.Tool.get(tool.id)
        assert fetched.id == tool.id
        assert fetched.integration_id == client.Tool.DEFAULT_INTEGRATION_ID, fetched.integration_id

        first = tool.run(action="add", data={"a": 2, "b": 3})
        assert first.status == "SUCCESS", first
        assert _returned_value(first) == "5", first.data

        tool.config = {"code": RAW_MULTIPLY, "function_name": "add"}
        tool.save()

        second = client.Tool.get(tool.id)
        updated = second.run(action="add", data={"a": 2, "b": 3})
        assert updated.status == "SUCCESS", updated
        assert _returned_value(updated) == "50", updated.data

    def test_create_from_callable(self, client, resource_tracker):
        tool = client.Tool(
            name=unique_name("func-utility-callable"),
            description="Multiply two integers.",
            code=multiply,
        )
        tool.save()
        resource_tracker.append(tool)

        result = tool.run(action="multiply", data={"a": 6, "b": 7})
        assert result.status == "SUCCESS", result
        assert _returned_value(result) == "42", result.data
