"""Unit tests for the v2 Model resource.

This module tests Model-specific functionality including:
- Property tests (is_sync_only, is_async_capable)
- Run/run_async routing based on connection_type
- V1 payload conversion for sync-only models
"""

import pytest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from aixplain.v2.enums import Function, ResponseStatus
from aixplain.v2.model import (
    Message,
    Model,
    ModelResponseStreamer,
    ModelResult,
    StreamChunk,
    Usage,
    find_function_by_id,
)


# =============================================================================
# Function Decoder Tests
# =============================================================================


class TestFindFunctionById:
    """Tests for find_function_by_id normalisation across backend ID formats."""

    def test_exact_enum_value(self):
        """Direct enum value like TEXT_GENERATION should resolve."""
        assert find_function_by_id("TEXT_GENERATION") == Function.TEXT_GENERATION

    def test_kebab_case_backend_format(self):
        """Backend-style kebab-case IDs (text-generation) should resolve."""
        assert find_function_by_id("text-generation") == Function.TEXT_GENERATION

    def test_mixed_case_kebab(self):
        """Mixed-case kebab IDs should still resolve."""
        assert find_function_by_id("Speech-Recognition") == Function.SPEECH_RECOGNITION

    def test_unknown_id_returns_none(self):
        """Completely unknown IDs should return None, not raise."""
        assert find_function_by_id("nonexistent-function") is None

    def test_all_enum_members_resolve_via_kebab(self):
        """Every Function member should be reachable via its kebab-case form."""
        for member in Function:
            kebab = member.value.lower().replace("_", "-")
            assert find_function_by_id(kebab) == member, f"{kebab} did not resolve to {member}"


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
        model.__post_init__()
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
# Capability Inference Tests
# =============================================================================


class TestModelCapabilityInference:
    """Tests for LLM-gated tool-calling and structured-output capability properties."""

    @staticmethod
    def _param(name: str):
        """Create a lightweight parameter-like object compatible with Inputs."""
        return SimpleNamespace(
            name=name,
            required=False,
            data_type="text",
            data_sub_type="text",
            default_values=[],
        )

    def _create_model(self, function=Function.TEXT_GENERATION, params=None, function_type="ai"):
        """Helper to create a Model with capability-related fields."""
        model = Model.__new__(Model)
        model.id = "test-model-id"
        model.name = "Test Model"
        model.function = function
        model.function_type = function_type
        model.params = params
        model.__post_init__()
        return model

    def test_supports_tool_calling_true_with_tools_param(self):
        """LLM should support tool calling when backend params include 'tools'."""
        model = self._create_model(params=[self._param("text"), self._param("tools")])
        assert model.supports_tool_calling is True

    def test_supports_tool_calling_true_with_tool_choice_camel_case(self):
        """LLM should support tool calling when backend params include 'toolChoice'."""
        model = self._create_model(params=[self._param("text"), self._param("toolChoice")])
        assert model.supports_tool_calling is True

    def test_supports_tool_calling_false_for_llm_without_tool_markers(self):
        """LLM should return False when params exist but no tool-calling markers."""
        model = self._create_model(params=[self._param("text"), self._param("temperature")])
        assert model.supports_tool_calling is False

    def test_supports_tool_calling_none_when_llm_params_unavailable(self):
        """LLM should return None when params are unavailable."""
        model = self._create_model(params=None)
        assert model.supports_tool_calling is None

    def test_supports_tool_calling_false_for_non_llm(self):
        """Non-LLM models should always return False for tool-calling capability."""
        model = self._create_model(function=Function.TRANSLATION, params=[self._param("tools")])
        assert model.supports_tool_calling is False

    def test_supports_tool_calling_none_when_function_missing_even_with_tool_params(self):
        """When function is missing, LLM gating should remain unknown."""
        model = self._create_model(function=None, params=[self._param("max_tokens"), self._param("tools")])
        assert model.supports_tool_calling is None

    def test_supports_structured_output_true_with_response_format_snake_case(self):
        """LLM should support structured output when params include 'response_format'."""
        model = self._create_model(params=[self._param("text"), self._param("response_format")])
        assert model.supports_structured_output is True

    def test_supports_structured_output_true_with_response_format_camel_case(self):
        """LLM should support structured output when params include 'responseFormat'."""
        model = self._create_model(params=[self._param("text"), self._param("responseFormat")])
        assert model.supports_structured_output is True

    def test_supports_structured_output_false_for_llm_without_markers(self):
        """LLM should return False when params exist but no structured-output markers."""
        model = self._create_model(params=[self._param("text"), self._param("temperature")])
        assert model.supports_structured_output is False

    def test_supports_structured_output_none_when_llm_params_unavailable(self):
        """LLM should return None when params are unavailable."""
        model = self._create_model(params=None)
        assert model.supports_structured_output is None

    def test_supports_structured_output_false_for_non_llm(self):
        """Non-LLM models should always return False for structured output capability."""
        model = self._create_model(function=Function.TRANSLATION, params=[self._param("response_format")])
        assert model.supports_structured_output is False

    def test_supports_structured_output_none_when_function_missing_and_params_missing(self):
        """When function and params are missing, capability should remain unknown."""
        model = self._create_model(function=None, params=None)
        assert model.supports_structured_output is None

    def test_supports_structured_output_none_when_function_missing_even_with_markers(self):
        """When function is missing, structured-output support should remain unknown."""
        model = self._create_model(function=None, params=[self._param("response_format")])
        assert model.supports_structured_output is None


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
        model.__post_init__()
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

    def test_build_run_payload_strips_sdk_params(self):
        """build_run_payload should exclude timeout, wait_time, show_progress, stream."""
        model = self._create_model_with_mocks(connection_type=["asynchronous"])
        payload = model.build_run_payload(
            text="hello",
            temperature=0.7,
            timeout=90,
            wait_time=0.5,
            show_progress=True,
            stream=True,
        )
        assert payload == {"text": "hello", "temperature": 0.7}
        for key in ("timeout", "wait_time", "show_progress", "stream"):
            assert key not in payload


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
        model.__post_init__()
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


# =============================================================================
# Streaming Tests
# =============================================================================


class TestModelStreaming:
    """Tests for v2 streaming parser and streaming payload options."""

    @staticmethod
    def _create_streamer(lines):
        """Create a response streamer from raw SSE lines."""
        response = Mock()
        response.iter_lines.return_value = iter(lines)
        return ModelResponseStreamer(response)

    @staticmethod
    def _create_streaming_model():
        """Create a model configured for run_stream tests."""
        model = Model.__new__(Model)
        model.id = "test-model-id"
        model.name = "Test Model"
        model.supports_streaming = True
        model.params = None
        model.__post_init__()
        model.context = Mock()
        model.context.client = Mock()
        return model

    def test_streamer_parses_aixplain_data_chunks(self):
        """ModelResponseStreamer should parse aiXplain-formatted stream chunks."""
        streamer = self._create_streamer(
            [
                'data: {"data":"Ship aiX"}',
                "data: [DONE]",
            ]
        )

        chunk = next(streamer)

        assert chunk.status == ResponseStatus.IN_PROGRESS
        assert chunk.data == "Ship aiX"
        assert chunk.tool_calls is None
        assert chunk.usage is None
        assert chunk.finish_reason is None

        with pytest.raises(StopIteration):
            next(streamer)
        assert streamer.status == ResponseStatus.SUCCESS

    def test_streamer_parses_openai_tool_call_deltas(self):
        """ModelResponseStreamer should parse OpenAI-formatted tool call deltas."""
        streamer = self._create_streamer(
            [
                (
                    'data: {"id":"chatcmpl-1","choices":[{"index":0,"delta":{"role":"assistant","content":null,'
                    '"tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"get_current_time",'
                    '"arguments":""}}]},"finish_reason":null}],"usage":null}'
                ),
                (
                    'data: {"id":"chatcmpl-1","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":'
                    '{"arguments":"{\\""}}]},"finish_reason":null}],"usage":null}'
                ),
                "data: [DONE]",
            ]
        )

        first_chunk = next(streamer)
        second_chunk = next(streamer)

        assert first_chunk.data == ""
        assert first_chunk.tool_calls is not None
        assert first_chunk.tool_calls[0]["function"]["name"] == "get_current_time"
        assert first_chunk.finish_reason is None
        assert first_chunk.usage is None

        assert second_chunk.data == ""
        assert second_chunk.tool_calls is not None
        assert second_chunk.tool_calls[0]["function"]["arguments"] == '{"'
        assert second_chunk.finish_reason is None
        assert second_chunk.usage is None

        with pytest.raises(StopIteration):
            next(streamer)
        assert streamer.status == ResponseStatus.SUCCESS

    def test_streamer_parses_openai_usage_and_finish_reason(self):
        """ModelResponseStreamer should keep usage and finish_reason from OpenAI chunks."""
        streamer = self._create_streamer(
            [
                'data: {"id":"chatcmpl-2","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}],"usage":null}',
                (
                    'data: {"id":"chatcmpl-2","choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}],'
                    '"usage":{"prompt_tokens":1,"completion_tokens":2,"total_tokens":3}}'
                ),
                "data: [DONE]",
            ]
        )

        content_chunk = next(streamer)
        usage_chunk = next(streamer)

        assert content_chunk.data == "Hello"
        assert content_chunk.finish_reason is None
        assert content_chunk.usage is None

        assert usage_chunk.data == ""
        assert usage_chunk.finish_reason == "tool_calls"
        assert usage_chunk.usage == {
            "prompt_tokens": 1,
            "completion_tokens": 2,
            "total_tokens": 3,
        }

        with pytest.raises(StopIteration):
            next(streamer)

    def test_streamer_normalizes_single_tool_call_object(self):
        """ModelResponseStreamer should normalize a single tool_call object to a list."""
        streamer = self._create_streamer(
            [
                (
                    'data: {"id":"chatcmpl-3","choices":[{"index":0,"delta":{"tool_calls":{"index":0,"id":"call_1",'
                    '"type":"function","function":{"name":"get_current_time","arguments":""}}},"finish_reason":null}],'
                    '"usage":null}'
                ),
                "data: [DONE]",
            ]
        )

        chunk = next(streamer)
        assert chunk.tool_calls is not None
        assert isinstance(chunk.tool_calls, list)
        assert chunk.tool_calls[0]["function"]["name"] == "get_current_time"

        with pytest.raises(StopIteration):
            next(streamer)

    def test_run_stream_sets_raw_true_when_tools_present(self):
        """run_stream() should auto-inject options.raw=True for streaming tool calls."""
        model = self._create_streaming_model()
        response = Mock()
        response.iter_lines.return_value = iter([])
        model.context.client.request_stream = Mock(return_value=response)

        payload = {
            "text": "hello",
            "tools": [{"type": "function", "function": {"name": "get_current_time"}}],
        }

        with patch.object(model, "_ensure_valid_state"):
            with patch.object(model, "build_run_payload", return_value=payload):
                with patch.object(model, "build_run_url", return_value="v2/models/test-model-id"):
                    model.run_stream(text="hello", tools=payload["tools"])

        call_args = model.context.client.request_stream.call_args
        sent_payload = call_args.kwargs["json"]
        assert sent_payload["options"]["stream"] is True
        assert sent_payload["options"]["raw"] is True

    def test_run_stream_keeps_existing_options_and_overrides_raw_for_tools(self):
        """run_stream() should preserve options and force raw=True when tools are present."""
        model = self._create_streaming_model()
        response = Mock()
        response.iter_lines.return_value = iter([])
        model.context.client.request_stream = Mock(return_value=response)

        payload = {
            "text": "hello",
            "tools": [{"type": "function", "function": {"name": "get_current_time"}}],
            "options": {
                "temperature": 0.2,
                "raw": False,
            },
        }

        with patch.object(model, "_ensure_valid_state"):
            with patch.object(model, "build_run_payload", return_value=payload):
                with patch.object(model, "build_run_url", return_value="v2/models/test-model-id"):
                    model.run_stream(text="hello", tools=payload["tools"])

        call_args = model.context.client.request_stream.call_args
        sent_payload = call_args.kwargs["json"]
        assert sent_payload["options"]["temperature"] == 0.2
        assert sent_payload["options"]["stream"] is True
        assert sent_payload["options"]["raw"] is True

    def test_run_stream_does_not_set_raw_when_tools_absent(self):
        """run_stream() should not inject options.raw when tools are not in payload."""
        model = self._create_streaming_model()
        response = Mock()
        response.iter_lines.return_value = iter([])
        model.context.client.request_stream = Mock(return_value=response)

        payload = {"text": "hello"}

        with patch.object(model, "_ensure_valid_state"):
            with patch.object(model, "build_run_payload", return_value=payload):
                with patch.object(model, "build_run_url", return_value="v2/models/test-model-id"):
                    model.run_stream(text="hello")

        call_args = model.context.client.request_stream.call_args
        sent_payload = call_args.kwargs["json"]
        assert sent_payload["options"]["stream"] is True
        assert "raw" not in sent_payload["options"]


# =============================================================================
# Integration Gap Regression Tests
# =============================================================================


class TestModelIntegrationGaps:
    """Regression tests for SDK integration gaps identified in ENG-2774."""

    @staticmethod
    def _create_streamer(lines):
        """Create a response streamer from raw SSE lines."""
        response = Mock()
        response.iter_lines.return_value = iter(lines)
        return ModelResponseStreamer(response)

    @staticmethod
    def _create_sync_model():
        """Create a sync-only model configured for direct-response path tests."""
        model = Model.__new__(Model)
        model.id = "test-model-id"
        model.name = "Test Model"
        model.connection_type = ["synchronous"]
        model.params = None
        model.__post_init__()
        model.context = Mock()
        model.context.client = Mock()
        return model

    def test_message_deserializes_tool_calls_with_null_content(self):
        """ModelResult parsing should keep tool_calls and None content on assistant messages."""
        payload = {
            "status": "SUCCESS",
            "completed": True,
            "model": "openai/gpt-5.2",
            "details": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_tokyo",
                                "type": "function",
                                "function": {
                                    "name": "get_current_time",
                                    "arguments": '{"city":"Tokyo"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
        }

        result = ModelResult.from_dict(payload)

        assert result.details is not None
        message = result.details[0].message
        assert isinstance(message, Message)
        assert message.content is None
        assert message.tool_calls is not None
        assert message.tool_calls[0]["function"]["name"] == "get_current_time"
        assert message.tool_calls[0]["function"]["arguments"] == '{"city":"Tokyo"}'

    def test_run_sync_v2_attaches_raw_data_for_direct_response(self):
        """_run_sync_v2() direct responses should preserve raw response payload."""
        model = self._create_sync_model()
        direct_response = {
            "status": "SUCCESS",
            "completed": True,
            "model": "openai/gpt-5.2",
            "details": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_tokyo",
                                "type": "function",
                                "function": {
                                    "name": "get_current_time",
                                    "arguments": '{"city":"Tokyo"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
        }
        model.context.client.request = Mock(return_value=direct_response)

        with patch.object(model, "_ensure_valid_state"):
            with patch.object(model, "build_run_payload", return_value={"text": "what time is it in tokyo?"}):
                with patch.object(model, "build_run_url", return_value="v2/models/test-model-id"):
                    result = model._run_sync_v2(text="what time is it in tokyo?")

        assert result._raw_data == direct_response
        assert result.model == "openai/gpt-5.2"

    def test_run_sync_v2_preserves_usage_and_asset(self):
        """_run_sync_v2() should deserialize usage and asset from direct response."""
        model = self._create_sync_model()
        direct_response = {
            "status": "SUCCESS",
            "completed": True,
            "data": "2 + 2 = 4.",
            "runTime": 1.766,
            "usedCredits": 3.725e-05,
            "usage": {"prompt_tokens": 13, "completion_tokens": 17, "total_tokens": 30},
            "asset": {"assetId": "test-model-id", "id": "openai/gpt-5-mini/openai"},
        }
        model.context.client.request = Mock(return_value=direct_response)

        with patch.object(model, "_ensure_valid_state"):
            with patch.object(model, "build_run_payload", return_value={"data": "What is 2+2?"}):
                with patch.object(model, "build_run_url", return_value="v2/models/test-model-id"):
                    result = model._run_sync_v2(data="What is 2+2?")

        assert isinstance(result, ModelResult)
        assert result.usage is not None
        assert isinstance(result.usage, Usage)
        assert result.usage.prompt_tokens == 13
        assert result.usage.completion_tokens == 17
        assert result.usage.total_tokens == 30
        assert result.used_credits == 3.725e-05
        assert result.run_time == 1.766
        assert result.asset == {"assetId": "test-model-id", "id": "openai/gpt-5-mini/openai"}

    def test_stream_chunk_coerces_non_string_data(self):
        """StreamChunk should enforce text chunks even when data is non-string."""
        chunk = StreamChunk(status=ResponseStatus.IN_PROGRESS, data={"usage": {"total_tokens": 3}})
        assert chunk.data == ""

    def test_streamer_coerces_non_openai_dict_data_to_empty_string(self):
        """ModelResponseStreamer should not leak dict payloads into chunk.data."""
        streamer = self._create_streamer(
            [
                'data: {"model":"openai/gpt-5.2","data":{"usage":{"total_tokens":3}}}',
                "data: [DONE]",
            ]
        )

        chunk = next(streamer)
        assert chunk.data == ""

        with pytest.raises(StopIteration):
            next(streamer)

    def test_streamer_buffers_multiline_openai_tool_call_chunks(self):
        """ModelResponseStreamer should buffer split SSE data lines into one JSON payload."""
        streamer = self._create_streamer(
            [
                (
                    'data: {"id":"chatcmpl-gap","model":"openai/gpt-5.2","choices":[{"index":0,"delta":{"role":"assistant",'
                    '"content":null,"tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"get_current_time",'
                    '"arguments":"{\\"city\\":\\"Tok'
                ),
                'data: yo\\"}"}}]},"finish_reason":"tool_calls"}],"usage":null}',
                "data: [DONE]",
            ]
        )

        chunk = next(streamer)

        assert chunk.data == ""
        assert chunk.tool_calls is not None
        assert chunk.tool_calls[0]["id"] == "call_1"
        assert chunk.tool_calls[0]["function"]["name"] == "get_current_time"
        assert chunk.tool_calls[0]["function"]["arguments"] == '{"city":"Tokyo"}'
        assert chunk.finish_reason == "tool_calls"

        with pytest.raises(StopIteration):
            next(streamer)


class TestModelStreamerSseEncoding:
    """Regression tests for SSE UTF-8 decoding (ENG-3044).

    The aiXplain backend serves ``text/event-stream`` without a ``charset``
    parameter — which is correct per the SSE spec (WHATWG HTML §9.2: SSE is
    always UTF-8, ``charset`` is not allowed). ``requests`` doesn't know that
    and falls back to ISO-8859-1 for any ``text/*`` body without an explicit
    charset (RFC 2616), so multi-byte UTF-8 characters emitted by the model
    (°, —, smart quotes, emojis) come back as mojibake when iterated via
    ``iter_lines(decode_unicode=True)``.

    ``ModelResponseStreamer`` knows it's consuming SSE, so it must override
    the ``requests`` fallback before iteration begins.
    """

    @staticmethod
    def _build_response(body: bytes, *, content_type: str = "text/event-stream") -> "requests.Response":
        """Build a real ``requests.Response`` whose ``raw`` returns ``body``.

        Mirrors what ``requests.adapters.HTTPAdapter.build_response`` produces:
        for ``text/*`` without a ``charset`` parameter, ``response.encoding``
        is set to ``ISO-8859-1`` — the bug surface this test exercises.
        """
        from io import BytesIO

        import requests
        from urllib3 import HTTPResponse

        raw = HTTPResponse(body=BytesIO(body), preload_content=False)
        response = requests.Response()
        response.raw = raw
        response.headers["Content-Type"] = content_type
        response.encoding = "ISO-8859-1"
        return response

    def test_streamer_decodes_multibyte_utf8(self):
        """End-to-end: multi-byte UTF-8 chars in the SSE body must decode correctly."""
        # Degree sign (U+00B0 → 0xC2 0xB0), em dash (U+2014 → 0xE2 0x80 0x94),
        # emoji (U+1F31E → 0xF0 0x9F 0x8C 0x9E).
        body = b'data: {"data": "Lisbon: 22.5\xc2\xb0C \xe2\x80\x94 \xf0\x9f\x8c\x9e"}\n\n'
        response = self._build_response(body)

        streamer = ModelResponseStreamer(response)
        chunks = list(streamer)

        assert len(chunks) == 1
        data = chunks[0].data
        assert "22.5°C" in data
        assert "—" in data
        assert "🌞" in data
        # Latin-1 mojibake signatures must not appear.
        assert "Â°" not in data
        assert "â\x80\x94" not in data

    def test_streamer_overrides_requests_iso_8859_1_fallback(self):
        """Override the ``requests`` ISO-8859-1 fallback with ``utf-8``.

        ``response.encoding`` must be set to ``utf-8`` when the
        ``requests`` ISO-8859-1 fallback is in effect.
        """
        response = self._build_response(b"data: [DONE]\n\n")
        assert response.encoding == "ISO-8859-1"

        ModelResponseStreamer(response)

        assert response.encoding == "utf-8"

    def test_streamer_overrides_none_encoding(self):
        """Override a missing encoding with ``utf-8``.

        ``response.encoding`` must be set to ``utf-8`` when no encoding is set
        at all (e.g. a hand-built response or a custom transport).
        """
        response = self._build_response(b"data: [DONE]\n\n")
        response.encoding = None

        ModelResponseStreamer(response)

        assert response.encoding == "utf-8"

    def test_streamer_preserves_explicit_charset(self):
        """Respect an explicit non-fallback charset.

        If a future backend header or a custom adapter sets a non-fallback
        charset, the streamer must respect it rather than silently clobbering
        an explicit choice.
        """
        response = self._build_response(b"data: [DONE]\n\n")
        response.encoding = "utf-16"

        ModelResponseStreamer(response)

        assert response.encoding == "utf-16"
