"""Unit tests for the v2 resource base classes and mixins.

This module tests the foundational resource infrastructure that all
resources (Agent, Model, Tool, etc.) inherit from.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from aixplain.v2.resource import (
    BaseResource,
    SearchResourceMixin,
    BaseSearchParams,
    GetResourceMixin,
    BaseGetParams,
    DeleteResourceMixin,
    BaseDeleteParams,
    DeleteResult,
    RunnableResourceMixin,
    BaseRunParams,
    Result,
    Page,
    with_hooks,
    encode_resource_id,
    _flatten_asset_info,
)
from aixplain.v2.exceptions import ResourceError, ValidationError, TimeoutError


# =============================================================================
# Basic BaseResource Tests
# =============================================================================


def test_base_resource():
    resource = BaseResource(id="123", name="test")
    assert resource.id == "123"
    assert resource.name == "test"


def test_base_resource_getattr():
    resource = BaseResource(id="123", name="test")
    assert resource.id == "123"
    assert resource.name == "test"


def test_base_resource_getattr_not_found():
    resource = BaseResource(id="123", name="test")
    with pytest.raises(AttributeError):
        resource.not_found


def test_base_resource_save():
    resource = BaseResource(name="test")
    resource.context = Mock()
    resource.context.client.request = Mock(return_value={"id": "123"})
    resource.save()
    # Check that the resource was created with the correct payload
    resource.context.client.request.assert_called_once_with(
        "post",
        "",
        json={
            "id": None,
            "name": "test",
            "description": None,
            "path": None,
        },
    )
    # Check that the ID was set from the response
    assert resource.id == "123"


def test_base_resource_save_with_id():
    resource = BaseResource(id="123", name="test")
    resource.context = Mock()
    resource.context.client.request = Mock(return_value={"id": "123"})
    resource.save()
    resource.context.client.request.assert_called_once_with("put", "/123", json=resource.to_dict())


def test_base_resource_action():
    class FixtureResource(BaseResource):
        RESOURCE_PATH = "demo"
        context = Mock()

    fixture_resource = FixtureResource(id="123", name="test")

    fixture_resource._action("get", ["do_something"], foo="bar")
    fixture_resource.context.client.request.assert_called_once_with(
        "get",
        "demo/123/do_something",
        foo="bar",
    )


def test_base_resource_search():
    class FixtureResource(BaseResource, SearchResourceMixin[BaseSearchParams, "FixtureResource"]):
        RESOURCE_PATH = "demo"
        context = Mock(
            client=Mock(
                request=Mock(
                    return_value=Mock(
                        json=Mock(
                            return_value={
                                "results": [
                                    {"id": "123", "name": "test"},
                                    {"id": "456", "name": "test2"},
                                ],
                                "total": 2,
                                "pageTotal": 1,
                            }
                        )
                    )
                )
            )
        )

    page = FixtureResource.search()

    assert page.total == 2
    assert page.page_number == 0
    assert page.page_total == 1
    assert len(page.results) == 2
    assert page.results[0].id == "123"
    assert page.results[0].name == "test"
    assert page.results[1].id == "456"
    assert page.results[1].name == "test2"

    FixtureResource.context.client.request.assert_called_once_with(
        "post",
        "demo/paginate",
        json={
            "pageNumber": 0,
            "pageSize": 20,
        },
    )
    FixtureResource.context.client.request.reset_mock()

    page = FixtureResource.search(
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
    class FixtureResource(BaseResource, GetResourceMixin[BaseGetParams, "FixtureResource"]):
        RESOURCE_PATH = "demo"
        context = Mock(client=Mock(get=Mock(return_value={"id": "123", "name": "test"})))

    obj = FixtureResource.get("123")
    assert obj.id == "123"
    assert obj.name == "test"

    FixtureResource.context.client.get.assert_called_once_with(
        "demo/123",
    )


# =============================================================================
# encode_resource_id Tests
# =============================================================================


class TestEncodeResourceId:
    """Tests for URL encoding of resource IDs."""

    def test_encode_simple_id(self):
        """Simple alphanumeric IDs should pass through unchanged."""
        assert encode_resource_id("abc123") == "abc123"

    def test_encode_id_with_dashes(self):
        """IDs with dashes should pass through unchanged."""
        assert encode_resource_id("abc-123-def") == "abc-123-def"

    def test_encode_id_with_slash(self):
        """Slashes should be URL encoded."""
        encoded = encode_resource_id("path/to/resource")
        assert "/" not in encoded
        assert "%2F" in encoded

    def test_encode_id_with_spaces(self):
        """Spaces should be URL encoded."""
        encoded = encode_resource_id("my resource")
        assert " " not in encoded
        assert "%20" in encoded

    def test_encode_id_with_special_chars(self):
        """Special characters should be URL encoded."""
        encoded = encode_resource_id("test@#$%")
        assert "@" not in encoded
        assert "#" not in encoded

    def test_encode_empty_string(self):
        """Empty string should return empty string."""
        assert encode_resource_id("") == ""


# =============================================================================
# _flatten_asset_info Tests
# =============================================================================


class TestFlattenAssetInfo:
    """Tests for flattening nested assetInfo structure."""

    def test_flatten_with_asset_info(self):
        """Should flatten assetInfo to path (instanceId has priority)."""
        data = {
            "id": "123",
            "assetInfo": {
                "assetPath": "path/to/asset",
                "instanceId": "openai/whisper-large/groq",
            },
        }
        result = _flatten_asset_info(data)

        # instanceId takes priority and becomes path
        assert result["path"] == "openai/whisper-large/groq"

    def test_flatten_without_asset_info(self):
        """Should return data unchanged if no assetInfo."""
        data = {"id": "123", "name": "test"}
        result = _flatten_asset_info(data)

        assert result == data

    def test_flatten_partial_asset_info(self):
        """Should use assetPath as fallback when instanceId is not present."""
        data = {
            "id": "123",
            "assetInfo": {
                "assetPath": "path/to/asset",
            },
        }
        result = _flatten_asset_info(data)

        # assetPath is used as fallback
        assert result["path"] == "path/to/asset"

    def test_flatten_non_dict_asset_info(self):
        """Should handle non-dict assetInfo gracefully."""
        data = {"id": "123", "assetInfo": "not a dict"}
        result = _flatten_asset_info(data)

        assert result == data

    def test_flatten_non_dict_input(self):
        """Should return non-dict input unchanged."""
        result = _flatten_asset_info("not a dict")
        assert result == "not a dict"


# =============================================================================
# with_hooks Decorator Tests
# =============================================================================


class TestWithHooksDecorator:
    """Tests for the hook decorator system."""

    def test_operation_executes_normally(self):
        """Operation should execute when no hooks return early."""

        class MockResource:
            def before_test_op(self, *args, **kwargs):
                return None

            def after_test_op(self, result, *args, **kwargs):
                return None

            @with_hooks
            def test_op(self):
                return "operation result"

        resource = MockResource()
        result = resource.test_op()

        assert result == "operation result"

    def test_before_hook_called(self):
        """before_<operation> should be called before operation."""
        before_called = []

        class MockResource:
            def before_my_action(self, *args, **kwargs):
                before_called.append(True)
                return None

            @with_hooks
            def my_action(self):
                return "done"

        resource = MockResource()
        resource.my_action()

        assert len(before_called) == 1

    def test_after_hook_called(self):
        """after_<operation> should be called after success."""
        after_calls = []

        class MockResource:
            def after_my_action(self, result, *args, **kwargs):
                after_calls.append(result)
                return None

            @with_hooks
            def my_action(self):
                return "action result"

        resource = MockResource()
        resource.my_action()

        assert len(after_calls) == 1
        assert after_calls[0] == "action result"

    def test_before_hook_early_return(self):
        """Non-None return from before hook should bypass operation."""
        operation_called = []

        class MockResource:
            def before_my_action(self, *args, **kwargs):
                return {"early": "result"}

            @with_hooks
            def my_action(self):
                operation_called.append(True)
                return "should not reach"

        resource = MockResource()
        result = resource.my_action()

        assert result == {"early": "result"}
        assert len(operation_called) == 0

    def test_after_hook_transforms_result(self):
        """Non-None return from after hook should replace result."""

        class MockResource:
            def after_my_action(self, result, *args, **kwargs):
                return {"transformed": result}

            @with_hooks
            def my_action(self):
                return "original"

        resource = MockResource()
        result = resource.my_action()

        assert result == {"transformed": "original"}

    def test_error_wrapped_in_resource_error(self):
        """Non-ResourceError exceptions should be wrapped."""

        class MockResource:
            @with_hooks
            def failing_action(self):
                raise ValueError("Original error")

        resource = MockResource()

        with pytest.raises(ResourceError) as exc_info:
            resource.failing_action()

        assert "Original error" in str(exc_info.value)

    def test_resource_error_not_wrapped(self):
        """ResourceError should not be double-wrapped."""

        class MockResource:
            @with_hooks
            def failing_action(self):
                raise ResourceError("Already resource error")

        resource = MockResource()

        with pytest.raises(ResourceError) as exc_info:
            resource.failing_action()

        assert "Already resource error" in str(exc_info.value)

    def test_hooks_receive_args(self):
        """Hooks should receive positional arguments."""
        received_args = []

        class MockResource:
            def before_my_action(self, *args, **kwargs):
                received_args.extend(args)
                return None

            @with_hooks
            def my_action(self, arg1, arg2):
                return f"{arg1}-{arg2}"

        resource = MockResource()
        resource.my_action("first", "second")

        assert "first" in received_args
        assert "second" in received_args

    def test_hooks_receive_kwargs(self):
        """Hooks should receive keyword arguments."""
        received_kwargs = {}

        class MockResource:
            def before_my_action(self, *args, **kwargs):
                received_kwargs.update(kwargs)
                return None

            @with_hooks
            def my_action(self, name=None, value=None):
                return f"{name}={value}"

        resource = MockResource()
        resource.my_action(name="test", value=42)

        assert received_kwargs["name"] == "test"
        assert received_kwargs["value"] == 42

    def test_missing_hooks_ok(self):
        """Operations should work without defined hooks."""

        class MockResource:
            @with_hooks
            def no_hooks_action(self):
                return "no hooks"

        resource = MockResource()
        result = resource.no_hooks_action()

        assert result == "no hooks"


# =============================================================================
# BaseResource Clone Tests
# =============================================================================


class TestBaseResourceClone:
    """Tests for resource cloning."""

    def test_clone_creates_copy(self):
        """Clone should create a deep copy."""
        original = BaseResource(id="123", name="original", description="desc")
        original.context = Mock()

        cloned = original.clone()

        assert cloned is not original
        assert cloned.name == original.name
        assert cloned.description == original.description

    def test_clone_resets_id(self):
        """Clone should set id to None."""
        original = BaseResource(id="123", name="test")
        original.context = Mock()

        cloned = original.clone()

        assert cloned.id is None

    def test_clone_resets_saved_state(self):
        """Clone should set _saved_state to None."""
        original = BaseResource(id="123", name="test")
        original.context = Mock()
        original._update_saved_state()

        cloned = original.clone()

        assert cloned._saved_state is None

    def test_clone_applies_kwargs(self):
        """Clone should apply kwargs to new instance."""
        original = BaseResource(id="123", name="original", description="old desc")
        original.context = Mock()

        cloned = original.clone(name="cloned", description="new desc")

        assert cloned.name == "cloned"
        assert cloned.description == "new desc"

    def test_clone_preserves_other_fields(self):
        """Clone should preserve fields not in kwargs."""
        original = BaseResource(id="123", name="original", description="keep this")
        original.context = Mock()

        cloned = original.clone(name="new name")

        assert cloned.name == "new name"
        assert cloned.description == "keep this"


# =============================================================================
# BaseResource Deleted State Tests
# =============================================================================


class TestBaseResourceDeletedState:
    """Tests for deleted resource handling."""

    def test_is_deleted_initially_false(self):
        """is_deleted should be False for new resources."""
        resource = BaseResource(id="123", name="test")

        assert resource.is_deleted is False

    def test_is_deleted_after_marking(self):
        """is_deleted should be True after marking."""
        resource = BaseResource(id="123", name="test")
        resource._deleted = True

        assert resource.is_deleted is True

    def test_operations_fail_on_deleted_resource(self):
        """Operations should raise ValidationError on deleted resources."""

        class TestResource(BaseResource):
            RESOURCE_PATH = "test"
            context = Mock()

        resource = TestResource(id="123", name="test")
        resource._deleted = True

        with pytest.raises(ValidationError, match="deleted"):
            resource._action("get")

    def test_ensure_valid_state_fails_without_id(self):
        """_ensure_valid_state should fail if no ID."""
        resource = BaseResource(name="test")
        resource._saved_state = None

        with pytest.raises(ValidationError, match="not been saved"):
            resource._ensure_valid_state()


# =============================================================================
# DeleteResourceMixin Tests
# =============================================================================


class TestDeleteResourceMixin:
    """Tests for delete operations."""

    def _create_deletable_resource(self):
        """Create a resource with delete capabilities."""

        @dataclass_json
        @dataclass
        class DeletableResource(BaseResource, DeleteResourceMixin[BaseDeleteParams, DeleteResult]):
            RESOURCE_PATH = "deletable"

        resource = DeletableResource(id="123", name="to delete")
        resource.context = Mock()
        resource.context.client.request_raw = Mock(return_value=Mock())
        return resource

    def test_delete_calls_api(self):
        """delete() should call DELETE endpoint."""
        resource = self._create_deletable_resource()

        resource.delete()

        resource.context.client.request_raw.assert_called_once()
        call_args = resource.context.client.request_raw.call_args
        assert call_args[0][0] == "delete"
        assert "deletable/123" in call_args[0][1]

    def test_delete_marks_resource_deleted(self):
        """delete() should set is_deleted to True."""
        resource = self._create_deletable_resource()

        resource.delete()

        assert resource.is_deleted is True

    def test_delete_clears_id(self):
        """delete() should set id to None."""
        resource = self._create_deletable_resource()

        resource.delete()

        assert resource.id is None

    def test_delete_returns_result(self):
        """delete() should return DeleteResult."""
        resource = self._create_deletable_resource()

        result = resource.delete()

        assert isinstance(result, DeleteResult)
        assert result.status == "SUCCESS"
        assert result.completed is True

    def test_delete_result_has_deleted_id(self):
        """DeleteResult should contain the deleted resource ID."""
        resource = self._create_deletable_resource()
        original_id = resource.id

        result = resource.delete()

        assert result.deleted_id == original_id

    def test_delete_fails_on_deleted_resource(self):
        """delete() should fail if resource already deleted."""
        resource = self._create_deletable_resource()
        resource._deleted = True
        resource.id = None

        # The hook decorator wraps ValidationError in ResourceError
        with pytest.raises(ResourceError, match="deleted"):
            resource.delete()


# =============================================================================
# RunnableResourceMixin Tests
# =============================================================================


class TestRunnableResourceMixin:
    """Tests for run operations."""

    def _create_runnable_resource(self):
        """Create a resource with run capabilities."""

        @dataclass_json
        @dataclass
        class RunnableResource(BaseResource, RunnableResourceMixin[BaseRunParams, Result]):
            RESOURCE_PATH = "runnable"
            RUN_ACTION_PATH = "run"

        resource = RunnableResource(id="123", name="runnable")
        resource.context = Mock()
        return resource

    def test_run_async_calls_api(self):
        """run_async() should POST to run endpoint."""
        resource = self._create_runnable_resource()
        resource.context.client.request = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": "result",
            }
        )

        resource.run_async()

        resource.context.client.request.assert_called_once()
        call_args = resource.context.client.request.call_args
        assert call_args[0][0] == "post"
        assert "runnable/123/run" in call_args[0][1]

    def test_run_returns_result(self):
        """run() should return Result object."""
        resource = self._create_runnable_resource()
        resource.context.client.request = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": "result data",
            }
        )

        result = resource.run()

        assert isinstance(result, Result)
        assert result.status == "SUCCESS"
        assert result.completed is True

    def test_run_polls_for_completion(self):
        """run() should poll until completed."""
        resource = self._create_runnable_resource()

        # First call returns polling URL (not completed)
        resource.context.client.request = Mock(
            return_value={
                "status": "IN_PROGRESS",
                "completed": False,
                "data": "https://poll.url/status",
            }
        )

        # Poll returns completed
        resource.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": "final result",
            }
        )

        result = resource.run()

        # Verify both the initial request and polling occurred
        resource.context.client.request.assert_called_once()
        resource.context.client.get.assert_called()
        assert result.completed is True
        assert result.status == "SUCCESS"

    def test_poll_returns_result(self):
        """poll() should return Result from poll URL."""
        resource = self._create_runnable_resource()
        resource.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
                "data": "poll result",
            }
        )

        result = resource.poll("https://poll.url")

        assert isinstance(result, Result)
        assert result.status == "SUCCESS"

    def test_sync_poll_respects_timeout(self):
        """sync_poll() should raise TimeoutError after timeout."""
        resource = self._create_runnable_resource()

        # Always return not completed
        resource.context.client.get = Mock(
            return_value={
                "status": "IN_PROGRESS",
                "completed": False,
            }
        )

        with pytest.raises(TimeoutError, match="timed out"):
            resource.sync_poll("https://poll.url", timeout=0.1, wait_time=0.05)

    def test_on_poll_hook_called(self):
        """on_poll() should be called after each poll."""
        resource = self._create_runnable_resource()
        poll_count = []

        def track_poll(response, **kwargs):
            poll_count.append(1)

        resource.on_poll = track_poll

        # Return completed after first poll
        resource.context.client.get = Mock(
            return_value={
                "status": "SUCCESS",
                "completed": True,
            }
        )

        resource.sync_poll("https://poll.url")

        assert len(poll_count) == 1

    def test_build_run_url_uses_resource_path(self):
        """build_run_url() should use RESOURCE_PATH and RUN_ACTION_PATH."""
        resource = self._create_runnable_resource()

        url = resource.build_run_url()

        assert "runnable/123/run" in url

    def test_build_run_payload_returns_kwargs(self):
        """build_run_payload() should return kwargs by default."""
        resource = self._create_runnable_resource()

        payload = resource.build_run_payload(key="value", other=123)

        assert payload == {"key": "value", "other": 123}


# =============================================================================
# Result Class Tests
# =============================================================================


class TestResult:
    """Tests for Result class."""

    def test_result_status(self):
        """Result should have status attribute."""
        result = Result(status="SUCCESS", completed=True)

        assert result.status == "SUCCESS"

    def test_result_completed(self):
        """Result should have completed attribute."""
        result = Result(status="SUCCESS", completed=True)

        assert result.completed is True

    def test_result_error_message(self):
        """Result should store error_message."""
        result = Result(status="FAILED", completed=True, error_message="Something went wrong")

        assert result.error_message == "Something went wrong"

    def test_result_url(self):
        """Result should store polling URL."""
        result = Result(status="IN_PROGRESS", completed=False, url="https://poll.url")

        assert result.url == "https://poll.url"

    def test_result_data(self):
        """Result should store data."""
        result = Result(status="SUCCESS", completed=True, data={"key": "value"})

        assert result.data == {"key": "value"}

    def test_result_getattr_from_raw_data(self):
        """Should access additional fields from _raw_data."""
        result = Result(status="SUCCESS", completed=True)
        result._raw_data = {"custom_field": "custom_value"}

        assert result.custom_field == "custom_value"

    def test_result_getattr_raises_for_missing(self):
        """Should raise AttributeError for truly missing attributes."""
        result = Result(status="SUCCESS", completed=True)
        result._raw_data = {}

        with pytest.raises(AttributeError):
            _ = result.nonexistent_field

    def test_result_repr_includes_status(self):
        """__repr__ should include status."""
        result = Result(status="SUCCESS", completed=True)

        repr_str = repr(result)

        assert "SUCCESS" in repr_str

    def test_result_repr_truncates_long_data(self):
        """__repr__ should truncate long data fields."""
        long_data = "x" * 500
        result = Result(status="SUCCESS", completed=True, data=long_data)

        repr_str = repr(result)

        assert len(repr_str) < len(long_data)
        assert "..." in repr_str


# =============================================================================
# DeleteResult Class Tests
# =============================================================================


class TestDeleteResult:
    """Tests for DeleteResult class."""

    def test_delete_result_inherits_from_result(self):
        """DeleteResult should inherit from Result."""
        result = DeleteResult(status="SUCCESS", completed=True)

        assert isinstance(result, Result)

    def test_delete_result_has_deleted_id(self):
        """DeleteResult should have deleted_id field."""
        result = DeleteResult(status="SUCCESS", completed=True, deleted_id="123")

        assert result.deleted_id == "123"


# =============================================================================
# Page Class Tests
# =============================================================================


class TestPage:
    """Tests for pagination."""

    def test_page_results_list(self):
        """Page should have results list."""
        page = Page(results=[1, 2, 3], page_number=0, page_total=1, total=3)

        assert page.results == [1, 2, 3]

    def test_page_total(self):
        """Page should have total count."""
        page = Page(results=[], page_number=0, page_total=5, total=100)

        assert page.total == 100

    def test_page_number(self):
        """Page should have page_number."""
        page = Page(results=[], page_number=2, page_total=5, total=100)

        assert page.page_number == 2

    def test_page_total_pages(self):
        """Page should have page_total."""
        page = Page(results=[], page_number=0, page_total=10, total=100)

        assert page.page_total == 10

    def test_page_getitem(self):
        """Page should support dict-like access."""
        page = Page(results=["a", "b"], page_number=1, page_total=3, total=6)

        assert page["results"] == ["a", "b"]
        assert page["page_number"] == 1
        assert page["total"] == 6

    def test_page_repr_is_json(self):
        """Page repr should be JSON-like."""
        page = Page(results=[], page_number=0, page_total=1, total=0)

        repr_str = repr(page)

        assert "results" in repr_str
        assert "total" in repr_str


# =============================================================================
# BaseResource Representation Tests
# =============================================================================


class TestBaseResourceRepr:
    """Tests for resource string representation."""

    def test_repr_with_id(self):
        """__repr__ should show id when present."""
        resource = BaseResource(id="123", name="test")

        repr_str = repr(resource)

        assert "123" in repr_str

    def test_repr_with_path(self):
        """__repr__ should prefer path over id."""
        resource = BaseResource(id="123", name="test")
        resource.path = "openai/whisper-large/groq"

        repr_str = repr(resource)

        assert "openai/whisper-large/groq" in repr_str

    def test_repr_without_path_shows_id(self):
        """__repr__ should show id when path is not set."""
        resource = BaseResource(id="123", name="test")

        repr_str = repr(resource)

        assert "123" in repr_str

    def test_str_equals_repr(self):
        """__str__ should equal __repr__."""
        resource = BaseResource(id="123", name="test")

        assert str(resource) == repr(resource)


# =============================================================================
# BaseResource Encoded ID Tests
# =============================================================================


class TestBaseResourceEncodedId:
    """Tests for encoded_id property."""

    def test_encoded_id_simple(self):
        """Simple ID should be returned as-is."""
        resource = BaseResource(id="abc123", name="test")

        assert resource.encoded_id == "abc123"

    def test_encoded_id_with_special_chars(self):
        """Special characters should be encoded."""
        resource = BaseResource(id="path/to/resource", name="test")

        encoded = resource.encoded_id

        assert "/" not in encoded

    def test_encoded_id_fails_without_id(self):
        """encoded_id should fail if no ID present."""
        resource = BaseResource(name="test")

        with pytest.raises(ValidationError):
            _ = resource.encoded_id

    def test_encoded_id_fails_if_deleted(self):
        """encoded_id should fail if resource deleted."""
        resource = BaseResource(id="123", name="test")
        resource._deleted = True

        with pytest.raises(ValidationError, match="deleted"):
            _ = resource.encoded_id
