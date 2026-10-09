"""Unit tests for the public ``from_row`` constructor on gettable resources."""

from unittest.mock import Mock

import pytest

from aixplain import Aixplain, Model, ResourceError, Tool


def _row(id: str = "a" * 24) -> dict:
    return {"id": id, "name": "gpt", "status": "onboarded", "assetInfo": {"instanceId": "openai/gpt/openai"}}


@pytest.fixture
def aix() -> Aixplain:
    """Return an isolated client."""
    return Aixplain(api_key="test-key", backend_url="https://example.test")


def test_from_row_builds_the_same_object_as_get(aix):
    aix.client.get = Mock(return_value=_row())

    fetched = aix.Model.get("a" * 24)
    built = aix.Model.from_row(_row())

    assert built.to_dict() == fetched.to_dict()
    assert built.path == "openai/gpt/openai"
    assert built.context is aix
    assert built.is_modified is False


def test_from_row_makes_no_request_and_leaves_the_row_untouched(aix):
    aix.client.get = Mock()
    row = _row()
    original = dict(row)

    aix.Tool.from_row(row)

    aix.client.get.assert_not_called()
    assert row == original
    assert "path" not in row


def test_from_row_returns_the_client_bound_class(aix):
    tool = aix.Tool.from_row(_row())

    assert isinstance(tool, Tool)
    assert isinstance(tool, aix.Tool)


def test_from_row_on_an_unbound_class_names_the_fix():
    with pytest.raises(ResourceError, match=r"aix\.Model"):
        Model.from_row(_row())


def test_from_row_rejects_a_non_dict(aix):
    with pytest.raises(ResourceError, match="expects a dict"):
        aix.Model.from_row([_row()])
