"""Unit tests for v2 utility code parsing helpers.

``parse_code`` and ``parse_code_decorated`` are what turn a callable, a file, a
URL or a raw source string into the ``(code_url, inputs, description, name)``
tuple a utility model used to be built from. They now have no caller inside
``aixplain/`` (custom code became a Tool), but they stay public and are the
subject of the SSRF guards, so they are pinned here.

``_upload_code`` performs a real S3 upload, so it is monkeypatched to keep
these tests credential-free and offline.
"""

import pytest

from aixplain.v2 import code_utils
from aixplain.v2.code_utils import (
    UtilityModelInput,
    parse_code,
    parse_code_decorated,
)
from aixplain.v2.enums import DataType


@pytest.fixture
def uploaded(monkeypatch):
    """Capture the source handed to ``_upload_code`` and return a fake URL."""
    seen = {}

    def fake_upload(str_code, backend_url=None, api_key=None):
        seen["code"] = str_code
        seen["backend_url"] = backend_url
        seen["api_key"] = api_key
        return "s3://bucket/code.py"

    monkeypatch.setattr(code_utils, "_upload_code", fake_upload)
    return seen


def main(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


class TestParseCodeCallable:
    def test_extracts_name_description_and_typed_inputs(self, uploaded):
        code_url, inputs, description, name = parse_code(main, api_key="k", backend_url="https://b")

        assert code_url == "s3://bucket/code.py"
        assert name == "main"
        assert description == "Add two numbers together."
        assert [(i.name, i.type) for i in inputs] == [("a", DataType.NUMBER), ("b", DataType.NUMBER)]
        assert uploaded["api_key"] == "k"
        assert uploaded["backend_url"] == "https://b"

    def test_bool_and_text_annotations_map_to_types(self, uploaded):
        def main(flag: bool, label: str) -> str:
            """A mixed signature."""
            return label

        _url, inputs, _description, _name = parse_code(main)
        assert [(i.name, i.type) for i in inputs] == [("flag", DataType.BOOLEAN), ("label", DataType.TEXT)]


class TestParseCodeString:
    def test_raw_source_docstring_is_used_as_description(self, uploaded):
        source = 'def main(a: int) -> int:\n    """Double it."""\n    return a * 2\n'

        _url, inputs, description, name = parse_code(source)

        assert name == "main"
        assert description == "Double it."
        assert [(i.name, i.type) for i in inputs] == [("a", DataType.NUMBER)]
        assert "def main" in uploaded["code"]

    def test_single_line_comment_is_used_as_description(self, uploaded):
        source = "def main(a: int) -> int:\n    # Halve it\n    return a // 2\n"

        _url, _inputs, description, _name = parse_code(source)

        assert description == "Halve it"

    def test_source_without_main_function_is_rejected(self, uploaded):
        with pytest.raises(Exception, match="must have a main function"):
            parse_code("def other(a: int) -> int:\n    return a\n")

    def test_missing_annotation_is_rejected(self, uploaded):
        source = "def main(a) -> int:\n    return 1\n"
        with pytest.raises(AssertionError, match="Input type is required"):
            parse_code(source)

    def test_unsupported_input_type_is_rejected(self, uploaded):
        source = "def main(a: dict) -> int:\n    return 1\n"
        with pytest.raises(Exception, match="Unsupported input type"):
            parse_code(source)

    def test_missing_docstring_yields_empty_description(self, uploaded):
        source = "def main(a: int) -> int:\n    return 1\n"
        _url, _inputs, description, _name = parse_code(source)
        assert description == ""

    def test_file_path_source_is_read_from_disk(self, uploaded, tmp_path):
        path = tmp_path / "code.py"
        path.write_text('def main(a: int) -> int:\n    """From a file."""\n    return a\n', encoding="utf-8")

        _url, _inputs, description, name = parse_code(str(path))

        assert name == "main"
        assert description == "From a file."


class TestUtilityModelInput:
    def test_string_type_is_coerced(self):
        item = UtilityModelInput(name="a", description="d", type="number")
        assert item.type is DataType.NUMBER

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown input type"):
            UtilityModelInput(name="a", description="d", type="datetime")

    def test_validate_accepts_supported_types(self):
        item = UtilityModelInput(name="a", description="d", type=DataType.TEXT)
        assert item.validate() is None

    def test_validate_rejects_unsupported_types(self):
        with pytest.raises(ValueError, match="TEXT, BOOLEAN or NUMBER"):
            UtilityModelInput(name="a", description="d", type=DataType.AUDIO).validate()

    def test_to_dict_serializes_type_value(self):
        item = UtilityModelInput(name="a", description="d", type=DataType.BOOLEAN)
        assert item.to_dict() == {"name": "a", "description": "d", "type": "boolean"}


class TestParseCodeDecorated:
    def test_decorated_source_extracts_metadata_and_renames_to_main(self, uploaded):
        source = (
            "@utility_tool(name='greet', description='Say hello')\n"
            "def greet(name: str) -> str:\n"
            "    return f'hi {name}'\n"
        )

        _url, inputs, description, name = parse_code_decorated(source)

        assert name == "greet"
        assert description == "Say hello"
        assert [(i.name, i.type) for i in inputs] == [("name", DataType.TEXT)]
        assert "def main" in uploaded["code"]
        assert "utility_tool" not in uploaded["code"]

    def test_decorator_inputs_override_signature_parsing(self, uploaded):
        source = (
            "@utility_tool(\n"
            "    name='scored',\n"
            "    description='Score it',\n"
            "    inputs=[UtilityModelInput(name='a', type=DataType.NUMBER, description='first')],\n"
            ")\n"
            "def scored(a) -> int:\n"
            "    return a\n"
        )

        _url, inputs, description, name = parse_code_decorated(source)

        assert name == "scored"
        assert description == "Score it"
        assert [(i.name, i.type, i.description) for i in inputs] == [("a", DataType.NUMBER, "first")]

    def test_decorated_callable_uses_attached_tool_metadata(self, uploaded):
        def tool(a: int) -> int:
            """fallback doc"""
            return a

        tool._is_utility_tool = True
        tool._tool_name = "attached"
        tool._tool_description = "attached description"
        tool._tool_inputs = [UtilityModelInput(name="a", type=DataType.NUMBER, description="an input")]

        _url, inputs, description, name = parse_code_decorated(tool)

        assert name == "attached"
        assert description == "attached description"
        assert [(i.name, i.type) for i in inputs] == [("a", DataType.NUMBER)]

    def test_decorated_callable_without_tool_inputs_infers_from_signature(self, uploaded):
        def tool(flag: bool) -> bool:
            """fallback doc"""
            return flag

        tool._is_utility_tool = True

        _url, inputs, description, name = parse_code_decorated(tool)

        assert description == "fallback doc"
        assert [(i.name, i.type) for i in inputs] == [("flag", DataType.BOOLEAN)]

    def test_plain_callable_falls_back_to_parse_code(self, uploaded):
        def add(a: int, b: int) -> int:
            """Add."""
            return a + b

        _url, inputs, description, name = parse_code_decorated(add)

        assert name == "add"
        assert description == "Add."
        assert len(inputs) == 2

    def test_undecorated_source_falls_back_to_parse_code(self, uploaded):
        source = 'def main(a: int) -> int:\n    """Doc."""\n    return a\n'

        _url, inputs, description, name = parse_code_decorated(source)

        assert name == "main"
        assert description == "Doc."
        assert len(inputs) == 1

    def test_class_input_is_rejected(self, uploaded):
        class Thing:
            pass

        with pytest.raises(TypeError, match="not a class or class instance"):
            parse_code_decorated(Thing)

    def test_decorator_without_function_is_rejected(self, uploaded):
        with pytest.raises(Exception, match="must have a main function"):
            parse_code_decorated("@utility_tool(name='x')\n")
