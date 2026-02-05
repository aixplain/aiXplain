"""Unit tests for the v2 Model resource.

This module tests Model-specific functionality including:
- Property tests (is_sync_only, is_async_capable)
- Run/run_async routing based on connection_type
- V1 payload conversion for sync-only models
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from aixplain.v2.model import Model, ModelResult


# =============================================================================
# Connection Type Property Tests
# =============================================================================


class TestModelConnectionTypeProperties:
    """Tests for is_sync_only and is_async_capable properties."""

    def _create_model(self, connection_type=None):
        """Helper to create a Model with specified connection_type."""
        model = Model.__new__(Model)
        model.id = "test-model-id"
        model.name = "Test Model"
        model.connection_type = connection_type
        model.params = None
        model._dynamic_attrs = {}
        return model

    # is_sync_only tests

    def test_is_sync_only_with_synchronous_only(self):
        """connection_type=['synchronous'] should return True for is_sync_only."""
        model = self._create_model(connection_type=["synchronous"])
        assert model.is_sync_only is True

    def test_is_sync_only_with_asynchronous_only(self):
        """connection_type=['asynchronous'] should return False for is_sync_only."""
        model = self._create_model(connection_type=["asynchronous"])
        assert model.is_sync_only is False

    def test_is_sync_only_with_both(self):
        """connection_type=['synchronous', 'asynchronous'] should return False for is_sync_only."""
        model = self._create_model(connection_type=["synchronous", "asynchronous"])
        assert model.is_sync_only is False

    def test_is_sync_only_with_none(self):
        """connection_type=None should return False for is_sync_only."""
        model = self._create_model(connection_type=None)
        assert model.is_sync_only is False

    # is_async_capable tests

    def test_is_async_capable_with_asynchronous_only(self):
        """connection_type=['asynchronous'] should return True for is_async_capable."""
        model = self._create_model(connection_type=["asynchronous"])
        assert model.is_async_capable is True

    def test_is_async_capable_with_synchronous_only(self):
        """connection_type=['synchronous'] should return False for is_async_capable."""
        model = self._create_model(connection_type=["synchronous"])
        assert model.is_async_capable is False

    def test_is_async_capable_with_both(self):
        """connection_type=['synchronous', 'asynchronous'] should return True for is_async_capable."""
        model = self._create_model(connection_type=["synchronous", "asynchronous"])
        assert model.is_async_capable is True

    def test_is_async_capable_with_none(self):
        """connection_type=None should return True for backward compatibility."""
        model = self._create_model(connection_type=None)
        assert model.is_async_capable is True


# =============================================================================
# Run Routing Tests
# =============================================================================


class TestModelRunRouting:
    """Tests for run() and run_async() routing logic."""

    def _create_model_with_mocks(self, connection_type=None):
        """Helper to create a Model with mocked context and methods."""
        model = Model.__new__(Model)
        model.id = "test-model-id"
        model.name = "Test Model"
        model.connection_type = connection_type
        model.params = None
        model._dynamic_attrs = {}
        model.context = Mock()
        return model

    def test_run_routes_to_sync_v2_for_sync_only_model(self):
        """run() should call _run_sync_v2() for sync-only models."""
        model = self._create_model_with_mocks(connection_type=["synchronous"])

        mock_result = ModelResult(status="SUCCESS", completed=True, data="test result")
        with patch.object(model, "_run_sync_v2", return_value=mock_result) as mock_sync_v2:
            with patch.object(model, "_merge_with_dynamic_attrs", return_value={"text": "hello"}):
                result = model.run(text="hello")

        mock_sync_v2.assert_called_once_with(text="hello")
        assert result.status == "SUCCESS"

    def test_run_routes_to_super_for_async_capable_model(self):
        """run() should call super().run() for async-capable models."""
        model = self._create_model_with_mocks(connection_type=["asynchronous"])

        mock_result = ModelResult(status="SUCCESS", completed=True, data="test result")
        with patch.object(Model, "_merge_with_dynamic_attrs", return_value={"text": "hello"}):
            with patch("aixplain.v2.resource.RunnableResourceMixin.run", return_value=mock_result) as mock_super_run:
                result = model.run(text="hello")

        mock_super_run.assert_called_once()
        assert result.status == "SUCCESS"

    def test_run_async_routes_to_v1_for_sync_only_model(self):
        """run_async() should call _run_async_v1() for sync-only models."""
        model = self._create_model_with_mocks(connection_type=["synchronous"])

        mock_result = ModelResult(status="IN_PROGRESS", completed=False, url="https://poll.url")
        with patch.object(model, "_run_async_v1", return_value=mock_result) as mock_v1:
            with patch.object(model, "_merge_with_dynamic_attrs", return_value={"text": "hello"}):
                result = model.run_async(text="hello")

        mock_v1.assert_called_once_with(text="hello")
        assert result.status == "IN_PROGRESS"

    def test_run_async_routes_to_super_for_async_capable_model(self):
        """run_async() should call super().run_async() for async-capable models."""
        model = self._create_model_with_mocks(connection_type=["asynchronous"])

        mock_result = ModelResult(status="IN_PROGRESS", completed=False, url="https://poll.url")
        with patch.object(Model, "_merge_with_dynamic_attrs", return_value={"text": "hello"}):
            with patch(
                "aixplain.v2.resource.RunnableResourceMixin.run_async", return_value=mock_result
            ) as mock_super_run_async:
                result = model.run_async(text="hello")

        mock_super_run_async.assert_called_once()
        assert result.status == "IN_PROGRESS"


# =============================================================================
# V1 Fallback Tests
# =============================================================================


class TestModelV1Fallback:
    """Tests for _run_async_v1() V1 endpoint integration."""

    def _create_model_with_context(self):
        """Helper to create a Model with mocked context."""
        model = Model.__new__(Model)
        model.id = "test-model-id"
        model.name = "Test Model"
        model.connection_type = ["synchronous"]
        model.params = None
        model._dynamic_attrs = {}
        model.context = Mock()
        model.context.model_url = "https://models.aixplain.com/api/v2/execute"
        model.context.api_key = "test-api-key"
        return model

    def test_run_async_v1_maps_text_to_data(self):
        """_run_async_v1() should map 'text' param to 'data' in V1 payload."""
        import json

        model = self._create_model_with_context()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "IN_PROGRESS",
            "data": "https://poll.url",
        }
        model.context.client.request_raw = Mock(return_value=mock_response)

        with patch.object(model, "_ensure_valid_state"):
            model._run_async_v1(text="hello", sourcelanguage="en")

        # Verify request_raw was called with JSON payload containing data and sourcelanguage
        model.context.client.request_raw.assert_called_once()
        call_args = model.context.client.request_raw.call_args
        sent_payload = json.loads(call_args[1]["data"])
        assert sent_payload["data"] == "hello"
        assert sent_payload["sourcelanguage"] == "en"

    def test_run_async_v1_transforms_url_v2_to_v1(self):
        """_run_async_v1() should transform /api/v2/ to /api/v1/ in URL."""
        model = self._create_model_with_context()
        model.context.model_url = "https://models.aixplain.com/api/v2/execute"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "IN_PROGRESS",
            "data": "https://poll.url",
        }
        model.context.client.request_raw = Mock(return_value=mock_response)

        with patch.object(model, "_ensure_valid_state"):
            model._run_async_v1(text="hello")

        # Verify the URL was transformed to v1
        call_args = model.context.client.request_raw.call_args
        url_arg = call_args[0][1]  # second positional arg is the url
        assert "/api/v1/" in url_arg
        assert "/api/v2/" not in url_arg
        assert url_arg == "https://models.aixplain.com/api/v1/execute/test-model-id"

    def test_run_async_v1_returns_model_result(self):
        """_run_async_v1() should return a ModelResult with correct fields."""
        model = self._create_model_with_context()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "IN_PROGRESS",
            "data": "https://poll.url",
        }
        model.context.client.request_raw = Mock(return_value=mock_response)

        with patch.object(model, "_ensure_valid_state"):
            result = model._run_async_v1(text="hello")

        assert isinstance(result, ModelResult)
        assert result.status == "IN_PROGRESS"
        assert result.completed is False
        assert result.url == "https://poll.url"

    def test_run_async_v1_handles_success_response(self):
        """_run_async_v1() should handle SUCCESS response from V1."""
        model = self._create_model_with_context()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "SUCCESS",
            "completed": True,
            "data": "translated text",
        }
        model.context.client.request_raw = Mock(return_value=mock_response)

        with patch.object(model, "_ensure_valid_state"):
            result = model._run_async_v1(text="hello")

        assert result.status == "SUCCESS"
        assert result.completed is True
        assert result.data == "translated text"

    def test_run_async_v1_excludes_timeout_and_wait_time_from_parameters(self):
        """_run_async_v1() should not include timeout/wait_time in V1 parameters."""
        import json

        model = self._create_model_with_context()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "IN_PROGRESS",
            "data": "https://poll.url",
        }
        model.context.client.request_raw = Mock(return_value=mock_response)

        with patch.object(model, "_ensure_valid_state"):
            model._run_async_v1(text="hello", timeout=300, wait_time=5, language="en")

        call_args = model.context.client.request_raw.call_args
        sent_payload = json.loads(call_args[1]["data"])
        assert "timeout" not in sent_payload
        assert "wait_time" not in sent_payload
        assert sent_payload["language"] == "en"
