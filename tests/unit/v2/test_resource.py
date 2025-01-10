import pytest
from unittest.mock import patch, Mock
from aixplain.v2.resource import BaseResource


def test_base_resource():
    resource = BaseResource(obj={"id": "123", "name": "test"})
    assert resource._obj == {"id": "123", "name": "test"}


def test_base_resource_getattr():
    resource = BaseResource(obj={"id": "123", "name": "test"})
    assert resource.id == "123"
    assert resource.name == "test"


def test_base_resource_getattr_not_found():
    resource = BaseResource(obj={"id": "123", "name": "test"})
    with pytest.raises(AttributeError):
        resource.not_found


def test_base_resource_save():
    resource = BaseResource(obj={"name": "test"})
    with patch("aixplain.v2.resource.BaseResource._action") as mock_action:
        resource.save()
        mock_action.assert_called_once_with("post", **resource._obj)


def test_base_resource_save_with_id():
    resource = BaseResource(obj={"id": "123", "name": "test"})
    with patch("aixplain.v2.resource.BaseResource._action") as mock_action:
        resource.save()
        mock_action.assert_called_once_with("put", ["123"], **resource._obj)


def test_base_resource_action():

    class FixtureResource(BaseResource):
        RESOURCE_PATH = "demo"
        context = Mock()

    fixture_resource = FixtureResource(obj={"id": "123", "name": "test"})

    fixture_resource._action("get", ["do_something"], foo="bar")
    fixture_resource.context.client.request.assert_called_once_with(
        "get",
        "sdk/demo/123/do_something",
        foo="bar",
    )
