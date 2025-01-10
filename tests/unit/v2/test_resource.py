import pytest
from unittest.mock import patch, Mock
from aixplain.v2.resource import (
    BaseResource,
    ListResourceMixin,
    BareListParams,
    GetResourceMixin,
    BareGetParams,
)


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


def test_base_resource_list():

    class FixtureResource(BaseResource, ListResourceMixin[BareListParams]):
        RESOURCE_PATH = "demo"
        context = Mock(
            client=Mock(
                request=Mock(
                    return_value=Mock(
                        json=Mock(
                            return_value={
                                "items": [
                                    {"id": "123", "name": "test"},
                                    {"id": "456", "name": "test2"},
                                ]
                            }
                        )
                    )
                )
            )
        )

    objects = FixtureResource.list()

    assert len(objects) == 2
    assert objects[0].id == "123"
    assert objects[0].name == "test"
    assert objects[1].id == "456"
    assert objects[1].name == "test2"

    FixtureResource.context.client.request.assert_called_once_with(
        "post",
        "demo/paginate",
        json={},
    )
    FixtureResource.context.client.request.reset_mock()

    objects = FixtureResource.list(
        page_number=1,
        page_size=20,
        query="test",
        sort_by="name",
        sort_order="asc",
        ownership="team",
    )

    FixtureResource.context.client.request.assert_called_once_with(
        "post",
        "demo/paginate",
        json={
            "pageNumber": 1,
            "pageSize": 20,
            "q": "test",
            "sortBy": "name",
            "sortOrder": "asc",
            "ownership": "team",
        },
    )


def test_base_resource_get():
    class FixtureResource(BaseResource, GetResourceMixin[BareGetParams]):
        RESOURCE_PATH = "demo"
        context = Mock(
            client=Mock(get_obj=Mock(return_value={"id": "123", "name": "test"}))
        )

    obj = FixtureResource.get(id="123")
    assert obj.id == "123"
    assert obj.name == "test"

    FixtureResource.context.client.get_obj.assert_called_once_with(
        "demo/123",
    )
