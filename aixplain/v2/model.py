"""Model resource for v2 API."""

from __future__ import annotations

import json
import logging
from typing import Union, List, Optional, Any, TYPE_CHECKING, Iterator
from typing_extensions import NotRequired, Unpack
from dataclasses_json import dataclass_json, config
from dataclasses import dataclass, field

from .resource import (
    BaseSearchParams,
    BaseResource,
    SearchResourceMixin,
    GetResourceMixin,
    BaseGetParams,
    Page,
    RunnableResourceMixin,
    BaseRunParams,
    Result,
)
from .enums import Function, Supplier, Language, AssetStatus, ResponseStatus
from .mixins import ToolableMixin, ToolDict
from .exceptions import ValidationError
from .actions import Actions, Action, Inputs

if TYPE_CHECKING:
    import requests

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class Message:
    """Message structure from the API response."""

    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[dict[str, Any]]] = None
    refusal: Optional[str] = None
    annotations: List[Any] = field(default_factory=list)


@dataclass_json
@dataclass
class Detail:
    """Detail structure from the API response."""

    index: Optional[int] = None
    message: Optional[Message] = None
    logprobs: Optional[Any] = None
    finish_reason: Optional[str] = field(default=None, metadata=config(field_name="finish_reason"))


@dataclass_json
@dataclass
class Usage:
    """Usage structure from the API response."""

    prompt_tokens: int = field(metadata=config(field_name="prompt_tokens"))
    completion_tokens: int = field(metadata=config(field_name="completion_tokens"))
    total_tokens: int = field(metadata=config(field_name="total_tokens"))


@dataclass_json
@dataclass
class ModelResult(Result):
    """Result for model runs with specific fields from the backend response."""

    details: Optional[List[Detail]] = None
    run_time: Optional[float] = field(default=None, metadata=config(field_name="runTime"))
    used_credits: Optional[float] = field(default=None, metadata=config(field_name="usedCredits"))
    usage: Optional[Usage] = None


@dataclass
class StreamChunk:
    """A chunk of streamed response data.

    Attributes:
        status: The current status of the streaming operation (IN_PROGRESS or SUCCESS)
        data: The content/token of this chunk
        tool_calls: Tool call deltas when stream uses OpenAI-style chunk format
        usage: Usage payload when provided in a stream chunk
        finish_reason: Completion reason for the current choice, when provided
    """

    status: ResponseStatus
    data: str
    tool_calls: Optional[List[dict[str, Any]]] = None
    usage: Optional[dict[str, Any]] = None
    finish_reason: Optional[str] = None

    def __post_init__(self) -> None:
        """Ensure data remains a text chunk."""
        if not isinstance(self.data, str):
            self.data = ""


class ModelResponseStreamer(Iterator[StreamChunk]):
    """A streamer for model responses that yields chunks as they arrive.

    This class provides an iterator interface for streaming model responses.
    It handles the conversion of Server-Sent Events (SSE) into StreamChunk objects
    and manages the response status.

    The streamer can be used directly in a for loop or as a context manager
    for proper resource cleanup.

    Example:
        >>> model = aix.Model.get("6895d6d1d50c89537c1cf237")  # GPT-5 Mini
        >>> for chunk in model.run(text="Explain LLMs", stream=True):
        ...     print(chunk.data, end="", flush=True)

        >>> # With context manager for proper cleanup
        >>> with model.run_stream(text="Hello") as stream:
        ...     for chunk in stream:
        ...         print(chunk.data, end="", flush=True)
    """

    def __init__(self, response: "requests.Response"):
        """Initialize a new ModelResponseStreamer instance.

        Args:
            response: A requests.Response object with streaming enabled
        """
        self._response = response
        self._iterator = response.iter_lines(decode_unicode=True)
        self.status = ResponseStatus.IN_PROGRESS
        self._done = False
        self._buffered_line: Optional[str] = None

    def __iter__(self) -> Iterator[StreamChunk]:
        """Return the iterator for the ModelResponseStreamer."""
        return self

    def __next__(self) -> StreamChunk:
        """Return the next chunk of the response.

        Returns:
            StreamChunk: A StreamChunk object containing the next chunk of the response.

        Raises:
            StopIteration: When the stream is complete
        """
        if self._done:
            raise StopIteration

        while True:
            try:
                if self._buffered_line is not None:
                    line = self._buffered_line
                    self._buffered_line = None
                else:
                    line = next(self._iterator)
            except StopIteration:
                self._done = True
                self.status = ResponseStatus.SUCCESS
                raise

            # Skip empty lines (SSE uses blank lines as separators)
            if not line:
                continue

            # Parse SSE data line - remove "data:" prefix and any leading whitespace
            if line.startswith("data:"):
                line = line[5:].lstrip()

            # Check for stream completion marker
            if line == "[DONE]":
                self._done = True
                self.status = ResponseStatus.SUCCESS
                raise StopIteration

            # Try to parse as JSON. If parsing fails, keep buffering consecutive
            # SSE data lines to reconstruct split JSON payloads.
            buffered_payload = line
            data = None
            while True:
                try:
                    data = json.loads(buffered_payload)
                    break
                except json.JSONDecodeError:
                    try:
                        continuation_line = next(self._iterator)
                    except StopIteration:
                        break

                    if not continuation_line:
                        break

                    if not continuation_line.startswith("data:"):
                        self._buffered_line = continuation_line
                        break

                    continuation_payload = continuation_line[5:].lstrip()
                    if continuation_payload == "[DONE]":
                        self._buffered_line = continuation_line
                        break

                    buffered_payload += continuation_payload

            if data is None:
                if buffered_payload.strip():
                    return StreamChunk(status=self.status, data=buffered_payload)
                continue

            # OpenAI-style stream chunk format:
            # {"choices":[{"delta":{"content":"...", "tool_calls":[...]},"finish_reason":...}],"usage":...}
            if isinstance(data, dict) and "choices" in data:
                choices = data.get("choices")
                choice = choices[0] if isinstance(choices, list) and choices else {}
                if not isinstance(choice, dict):
                    choice = {}

                delta = choice.get("delta")
                if not isinstance(delta, dict):
                    delta = {}

                content = delta.get("content")
                content = content if isinstance(content, str) else ""

                tool_calls = delta.get("tool_calls")
                if tool_calls is not None and not isinstance(tool_calls, list):
                    tool_calls = [tool_calls]

                finish_reason = choice.get("finish_reason")
                finish_reason = finish_reason if isinstance(finish_reason, str) else None

                usage = data.get("usage")
                usage = usage if isinstance(usage, dict) else None

                return StreamChunk(
                    status=self.status,
                    data=content,
                    tool_calls=tool_calls,
                    usage=usage,
                    finish_reason=finish_reason,
                )

            content = data.get("data", "") if isinstance(data, dict) else ""
            content = content if isinstance(content, str) else ""

            # Check if this is the completion signal inside JSON
            if content == "[DONE]":
                self._done = True
                self.status = ResponseStatus.SUCCESS
                raise StopIteration

            return StreamChunk(status=self.status, data=content)

    def close(self) -> None:
        """Close the underlying response connection."""
        if hasattr(self._response, "close"):
            self._response.close()

    def __enter__(self) -> "ModelResponseStreamer":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures response is closed."""
        self.close()


InputsProxy = Inputs


def find_supplier_by_id(supplier_id: Union[str, int]) -> Optional[Supplier]:
    """Find supplier enum by ID."""
    supplier_id_str = str(supplier_id)
    return next(
        (supplier for supplier in Supplier if supplier.value.get("id") == supplier_id_str),
        None,
    )


def find_function_by_id(function_id: str) -> Optional[Function]:
    """Find function enum by ID.

    Handles both SDK-style identifiers (``TEXT_GENERATION``) and the
    kebab-case identifiers returned by the backend API
    (``text-generation``).
    """
    # First try the raw value — some members use lowercase values
    # (e.g. UTILITIES = "utilities") that would break if uppercased.
    try:
        return Function(function_id)
    except ValueError:
        pass

    # Fall back to normalising backend kebab-case IDs (e.g. "text-generation" → "TEXT_GENERATION").
    normalized = function_id.upper().replace("-", "_")
    try:
        return Function(normalized)
    except ValueError:
        return None


@dataclass_json
@dataclass
class Attribute:
    """Common attribute structure from the API response."""

    name: str
    code: Optional[Any] = None
    value: Optional[Any] = None


@dataclass_json
@dataclass
class Parameter:
    """Common parameter structure from the API response."""

    name: str
    required: bool = False
    multiple_values: bool = field(default=False, metadata=config(field_name="multipleValues"))
    is_fixed: bool = field(default=False, metadata=config(field_name="isFixed"))
    data_type: Optional[str] = field(default=None, metadata=config(field_name="dataType"))
    data_sub_type: Optional[str] = field(default=None, metadata=config(field_name="dataSubType"))
    values: List[Any] = field(default_factory=list)
    default_values: List[Any] = field(default_factory=list, metadata=config(field_name="defaultValues"))
    available_options: List[Any] = field(default_factory=list, metadata=config(field_name="availableOptions"))


@dataclass_json
@dataclass
class Version:
    """Version structure from the API response."""

    name: Optional[str] = None
    id: Optional[str] = None


@dataclass_json
@dataclass
class Pricing:
    """Pricing structure from the API response."""

    price: Optional[float] = None
    unit_type: Optional[str] = field(default=None, metadata=config(field_name="unitType"))
    unit_type_scale: Optional[str] = field(default=None, metadata=config(field_name="unitTypeScale"))


@dataclass_json
@dataclass
class VendorInfo:
    """Supplier information structure from the API response."""

    id: Optional[Union[str, int]] = None
    name: Optional[str] = None
    code: Optional[str] = None


class ModelSearchParams(BaseSearchParams):
    """Search parameters for model queries."""

    functions: NotRequired[List[str]]
    vendors: NotRequired[Union[str, Supplier, List[Union[str, Supplier]]]]
    source_languages: NotRequired[Union[Language, List[Language]]]
    target_languages: NotRequired[Union[Language, List[Language]]]
    is_finetunable: NotRequired[bool]
    saved: NotRequired[bool]
    status: NotRequired[List[str]]
    q: NotRequired[str]  # Search query parameter as per Swagger spec
    host: NotRequired[str]  # Filter by host (e.g., "openai", "aiXplain")
    developer: NotRequired[str]  # Filter by developer (e.g., "OpenAI")
    path: NotRequired[str]  # Filter by path prefix (e.g., "openai/gpt-4")


class ModelRunParams(BaseRunParams):
    """Parameters for running models.

    Attributes:
        stream: If True, returns a ModelResponseStreamer for streaming responses.
            The model must support streaming (check supports_streaming attribute).
    """

    stream: NotRequired[bool]


@dataclass_json
@dataclass(repr=False)
class Model(
    BaseResource,
    SearchResourceMixin[ModelSearchParams, "Model"],
    GetResourceMixin[BaseGetParams, "Model"],
    RunnableResourceMixin[ModelRunParams, ModelResult],
    ToolableMixin,
):
    """Resource for models."""

    RESOURCE_PATH = "v2/models"
    RESPONSE_CLASS = ModelResult

    # Core fields from BaseResource (id, name, description)
    service_name: Optional[str] = field(default=None, metadata=config(field_name="serviceName"))
    status: Optional[AssetStatus] = None
    host: Optional[str] = None
    developer: Optional[str] = None
    vendor: Optional[VendorInfo] = None
    function: Optional[Function] = field(
        default=None,
        metadata=config(decoder=lambda x: find_function_by_id(x["id"]) if isinstance(x, dict) and "id" in x else x),
    )

    # Pricing information
    pricing: Optional[Pricing] = None

    # Version information
    version: Optional[Version] = None

    # Function type and model type
    function_type: Optional[str] = field(default=None, metadata=config(field_name="functionType"))
    type: Optional[str] = "model"

    # Timestamps
    created_at: Optional[str] = field(default=None, metadata=config(field_name="createdAt"))
    updated_at: Optional[str] = field(default=None, metadata=config(field_name="updatedAt"))

    # Capabilities
    supports_streaming: Optional[bool] = field(default=None, metadata=config(field_name="supportsStreaming"))
    supports_byoc: Optional[bool] = field(default=None, metadata=config(field_name="supportsBYOC"))

    # Connection type - indicates whether model supports sync/async execution
    # Values can be: ["synchronous"], ["asynchronous"], or ["synchronous", "asynchronous"]
    connection_type: Optional[List[str]] = field(default=None, metadata=config(field_name="connectionType"))

    # Attributes and parameters with proper types
    attributes: Optional[List[Attribute]] = None
    params: Optional[List[Parameter]] = None

    def __post_init__(self):
        """Initialize dynamic attributes based on backend parameters."""
        inputs = Inputs.from_parameters(self.params)
        run_action = Action(name="run", inputs=inputs)
        object.__setattr__(self, "_model_actions", Actions({"run": run_action}))
        object.__setattr__(self, "inputs", inputs)

    @property
    def actions(self) -> Actions:
        """Actions available on this model (always a single ``"run"`` action)."""
        return self._model_actions

    @staticmethod
    def _normalize_param_name(name: str) -> str:
        """Normalize parameter names for snake_case/camelCase compatibility."""
        return "".join(char for char in name.lower() if char.isalnum())

    @property
    def _normalized_param_names(self) -> Optional[set[str]]:
        """Return normalized backend input parameter names for capability inference."""
        if self.params is None:
            return None

        normalized_names: set[str] = set()
        for param in self.params:
            param_name = getattr(param, "name", None)
            if isinstance(param_name, str):
                normalized_names.add(self._normalize_param_name(param_name))
        return normalized_names

    @property
    def _is_text_generation_model(self) -> Optional[bool]:
        """Return whether this model is an LLM/text-generation model.

        Uses backend-provided function metadata only.
        """
        if self.function is None:
            return None

        if self.function is not None:
            if isinstance(self.function, Function):
                function_value = self.function.value
            elif isinstance(self.function, dict):
                function_value = str(self.function.get("id"))
            else:
                function_value = str(self.function)
            return function_value == Function.TEXT_GENERATION.value
        return None

    @property
    def supports_tool_calling(self) -> Optional[bool]:
        """Return whether this LLM supports tool calling, inferred from backend params."""
        is_text_generation_model = self._is_text_generation_model
        if is_text_generation_model is False:
            return False
        if is_text_generation_model is None:
            return None

        normalized_names = self._normalized_param_names
        if normalized_names is None:
            return None

        return "tools" in normalized_names or "toolchoice" in normalized_names

    @property
    def supports_structured_output(self) -> Optional[bool]:
        """Return whether this LLM supports structured output, inferred from backend params."""
        is_text_generation_model = self._is_text_generation_model
        if is_text_generation_model is False:
            return False
        if is_text_generation_model is None:
            return None

        normalized_names = self._normalized_param_names
        if normalized_names is None:
            return None

        return "responseformat" in normalized_names

    @property
    def is_sync_only(self) -> bool:
        """Check if the model only supports synchronous execution.

        Returns:
            bool: True if the model only supports synchronous execution
        """
        if self.connection_type is None:
            return False
        return "synchronous" in self.connection_type and "asynchronous" not in self.connection_type

    @property
    def is_async_capable(self) -> bool:
        """Check if the model supports asynchronous execution.

        Returns:
            bool: True if the model supports asynchronous execution
        """
        if self.connection_type is None:
            return True  # Default to async capable for backward compatibility
        return "asynchronous" in self.connection_type

    def __setattr__(self, name: str, value):
        """Handle bulk assignment to inputs."""
        if name == "inputs" and isinstance(value, dict):
            self.inputs.update(**value)
        else:
            super().__setattr__(name, value)

    _SDK_ONLY_PARAMS = frozenset({"timeout", "wait_time", "show_progress", "stream"})

    def build_run_payload(self, **kwargs: Unpack[ModelRunParams]) -> dict:
        """Build the JSON payload for a model execution request.

        Strips SDK-only orchestration params (``timeout``, ``wait_time``,
        ``show_progress``, ``stream``) so they are never forwarded to the
        backend API.
        """
        filtered = {k: v for k, v in kwargs.items() if k not in self._SDK_ONLY_PARAMS}
        return super().build_run_payload(**filtered)

    def build_run_url(self, **kwargs: Unpack[ModelRunParams]) -> str:
        """Build the URL for running the model."""
        self._ensure_valid_state()
        return f"{self.context.model_url}/{self.id}"

    def mark_as_deleted(self) -> None:
        """Mark the model as deleted by setting status to DELETED and calling parent method."""
        from .enums import AssetStatus

        self.status = AssetStatus.DELETED
        super().mark_as_deleted()

    @classmethod
    def get(
        cls: type["Model"],
        id: str,
        **kwargs: Unpack[BaseGetParams],
    ) -> "Model":
        """Get a model by ID."""
        return super().get(id, **kwargs)

    @classmethod
    def search(
        cls: type["Model"],
        query: Optional[str] = None,
        **kwargs: Unpack[ModelSearchParams],
    ) -> Page["Model"]:
        """Search with optional query and filtering.

        Args:
            query: Optional search query string
            **kwargs: Additional search parameters (functions, suppliers, etc.)

        Returns:
            Page of items matching the search criteria
        """
        # If query is provided, add it to kwargs
        if query is not None:
            kwargs["query"] = query

        # Use v2 endpoint - it uses "results" as the items key (default)
        return super().search(**kwargs)

    def run(self, **kwargs: Unpack[ModelRunParams]) -> ModelResult:
        """Run the model with dynamic parameter validation and default handling.

        This method routes the execution based on the model's connection type:
        - Sync models: Uses V2 endpoint directly (returns result immediately)
        - Async models: Uses V2 endpoint and polls until completion
        """
        # Merge dynamic attributes with provided kwargs
        effective_params = self._merge_with_dynamic_attrs(**kwargs)

        # Validate all parameters against model's expected inputs
        if self.params:
            param_errors = self._validate_params(**effective_params)
            if param_errors:
                raise ValueError(f"Parameter validation failed: {'; '.join(param_errors)}")

        if self.is_sync_only:
            # Sync-only models: Call V2 endpoint directly (bypass run_async which would route to V1)
            # V2 returns result directly for sync models, no polling needed
            return self._run_sync_v2(**effective_params)
        else:
            # Async-capable models: Use base run() which calls run_async() and polls
            return super().run(**effective_params)

    def _run_sync_v2(self, **kwargs: Unpack[ModelRunParams]) -> ModelResult:
        """Run the model synchronously using V2 endpoint directly.

        This bypasses run_async() to avoid V1 fallback for sync-only models.

        Returns:
            ModelResult: Direct result from V2 endpoint
        """
        self._ensure_valid_state()

        payload = self.build_run_payload(**kwargs)
        run_url = self.build_run_url(**kwargs)

        response = self.context.client.request("post", run_url, json=payload)

        return self.handle_run_response(response, **kwargs)

    def run_async(self, **kwargs: Unpack[ModelRunParams]) -> ModelResult:
        """Run the model asynchronously.

        This method routes the execution based on the model's connection type:
        - Sync models: Falls back to V1 endpoint (V2 doesn't support async for sync models)
        - Async models: Uses V2 endpoint directly (returns polling URL)

        Returns:
            ModelResult: Result with polling URL for async models,
                        or immediate result via V1 for sync-only models
        """
        # Merge dynamic attributes with provided kwargs
        effective_params = self._merge_with_dynamic_attrs(**kwargs)

        # Validate all parameters against model's expected inputs
        if self.params:
            param_errors = self._validate_params(**effective_params)
            if param_errors:
                raise ValueError(f"Parameter validation failed: {'; '.join(param_errors)}")

        if self.is_sync_only:
            # Sync-only models: Use V1 endpoint for async execution
            return self._run_async_v1(**effective_params)
        else:
            # Async-capable models: Use V2 endpoint
            return super().run_async(**effective_params)

    def _run_async_v1(self, **kwargs: Unpack[ModelRunParams]) -> ModelResult:
        """Run the model asynchronously using V1 endpoint.

        This is used as a fallback for sync-only models that need async execution.
        Uses the v2 client directly to avoid importing v1 modules (which trigger
        env var validation).

        Returns:
            ModelResult: Result with polling URL from V1 endpoint
        """
        self._ensure_valid_state()

        # Build V1 payload: V1 expects 'data' parameter, map from 'text' if needed
        data = kwargs.pop("text", None)
        parameters = {k: v for k, v in kwargs.items() if k not in ["timeout", "wait_time"]}

        payload = {"data": data}
        if parameters:
            payload.update(parameters)
        json_payload = json.dumps(payload)

        # Derive V1 URL from context's model_url (replace v2 with v1)
        v1_base_url = self.context.model_url.replace("/api/v2/", "/api/v1/")
        url = f"{v1_base_url}/{self.id}"

        # Use the v2 client's raw request method (raises APIError on non-2xx)
        try:
            r = self.context.client.request_raw("post", url, data=json_payload)
            resp = r.json()
        except Exception as e:
            logger.error(f"Error in V1 async request: {e}")
            return ModelResult(
                status=ResponseStatus.FAILED.value,
                completed=True,
                data="",
                error_message=f"Model Run: {e}",
            )

        # request_raw only returns on 2xx; parse the response
        status = resp.get("status", "IN_PROGRESS")
        resp_data = resp.get("data", None)
        if status == "IN_PROGRESS":
            if resp_data is not None:
                return ModelResult(
                    status=ResponseStatus.IN_PROGRESS.value,
                    completed=False,
                    data="",
                    url=resp_data,
                )
            else:
                return ModelResult(
                    status=ResponseStatus.FAILED.value,
                    completed=True,
                    data="",
                    error_message="Model Run: An error occurred while processing your request.",
                )
        else:
            try:
                raw_status = ResponseStatus(status)
            except ValueError:
                raw_status = ResponseStatus.FAILED
            return ModelResult(
                status=raw_status.value,
                completed=resp.get("completed", True),
                data=resp.get("data", ""),
                url=resp.get("url", None),
                error_message=resp.get("error_message", None),
            )

    def run_stream(self, **kwargs: Unpack[ModelRunParams]) -> ModelResponseStreamer:
        """Run the model with streaming response.

        This method executes the model and returns a streamer that yields response
        chunks as they are generated. This is useful for real-time output display
        or processing large responses incrementally.

        Args:
            **kwargs: Model-specific parameters (same as run() without stream parameter)

        Returns:
            ModelResponseStreamer: A streamer that yields StreamChunk objects. Can be
                iterated directly or used as a context manager.

        Raises:
            ValidationError: If the model explicitly does not support streaming
                (supports_streaming is False)
            ValueError: If required parameters are missing or have invalid types

        Example:
            >>> model = aix.Model.get("6895d6d1d50c89537c1cf237")  # GPT-5 Mini
            >>> with model.run_stream(text="Explain quantum computing") as stream:
            ...     for chunk in stream:
            ...         print(chunk.data, end="", flush=True)

            >>> # Or without context manager
            >>> for chunk in model.run_stream(text="Hello"):
            ...     print(chunk.data, end="", flush=True)
        """
        if self.supports_streaming is False:
            raise ValidationError(
                f"Model '{self.name}' (id={self.id}) does not support streaming. "
                "Check the model's supports_streaming attribute before calling run_stream()."
            )

        effective_params = self._merge_with_dynamic_attrs(**kwargs)

        if self.params:
            param_errors = self._validate_params(**effective_params)
            if param_errors:
                raise ValueError(f"Parameter validation failed: {'; '.join(param_errors)}")

        self._ensure_valid_state()

        payload = self.build_run_payload(**effective_params)

        if "options" not in payload:
            payload["options"] = {}
        payload["options"]["stream"] = True
        if payload.get("tools") is not None:
            payload["options"]["raw"] = True

        run_url = self.build_run_url(**effective_params)

        logger.debug(f"Model Run Stream: Start service for {run_url}")

        response = self.context.client.request_stream("POST", run_url, json=payload)

        return ModelResponseStreamer(response)

    def _merge_with_dynamic_attrs(self, **kwargs) -> dict:
        """Merge provided parameters with dynamic attributes.

        Args:
            **kwargs: Parameters provided to the run method

        Returns:
            Dictionary with all parameters, including dynamic attributes
        """
        # Start with current dynamic attribute values
        merged = dict(self.inputs.items())

        # Override with explicitly provided parameters
        merged.update(kwargs)

        # Filter out None values - they represent unset parameters that shouldn't be sent to the API
        filtered_merged = {k: v for k, v in merged.items() if v is not None}

        return filtered_merged

    def _validate_params(self, **kwargs) -> List[str]:
        """Validate all provided parameters against the model's expected parameters."""
        if not self.params:
            return []

        errors = []

        # Validate all parameters (required and optional)
        for param in self.params:
            if param.name in kwargs:
                value = kwargs[param.name]
                # Only validate if the value is not None (None means parameter is not set)
                if value is not None and not self._validate_param_type(param, value):
                    errors.append(
                        f"Parameter '{param.name}' has invalid type. "
                        f"Expected {param.data_type}, "
                        f"got {type(value).__name__}"
                    )
            elif param.required:
                errors.append(f"Required parameter '{param.name}' is missing")

        return errors

    def _validate_param_type(self, param: Parameter, value: Any) -> bool:
        """Validate parameter type based on the parameter definition."""
        # If data_type is not specified, accept any value
        if param.data_type is None:
            return True

        # Check data_type first
        if param.data_type == "text":
            # For text type, check data_sub_type for more specific validation
            if param.data_sub_type == "json":
                # text/json should accept dict, list, or string
                return isinstance(value, (dict, list, str))
            elif param.data_sub_type == "number":
                # text/number should accept int, float, or string
                return isinstance(value, (int, float, str))
            else:
                # text/other should accept only string
                return isinstance(value, str)
        elif param.data_type == "json":
            return isinstance(value, (dict, list, str))
        elif param.data_type == "number":
            return isinstance(value, (int, float))
        elif param.data_type == "boolean":
            return isinstance(value, bool)
        elif param.data_type == "array":
            return isinstance(value, list)
        else:
            # For unknown types, accept any value
            return True

    def as_tool(self) -> ToolDict:
        """Serialize this model as a tool for agent creation.

        This method converts the model into a dictionary format that can be used
        as a tool when creating agents. The format matches what the agent factory
        expects for model tools.

        Returns:
            dict: A dictionary representing this model as a tool with the following structure:
                - id: The model's ID
                - name: The model's name
                - description: The model's description
                - supplier: The supplier code
                - parameters: Current parameter values
                - function: The model's function type
                - type: Always "model"
                - version: The model's version
                - asset_id: The model's ID (same as id)

        Example:
            >>> model = aix.Model.get("some-model-id")
            >>> agent = aix.Agent(..., tools=[model.as_tool()])
        """
        # Get current parameter values using get_parameters()
        parameters = self.get_parameters()

        # Get supplier code
        supplier_code = "aixplain"  # Default supplier
        if self.vendor and self.vendor.code:
            supplier_code = self.vendor.code

        # Get function type
        function_type = None
        if self.function:
            function_type = self.function.value if hasattr(self.function, "value") else str(self.function)

        # Get version - handle Version objects properly
        version = None
        if self.version:
            if hasattr(self.version, "id") and self.version.id:
                version = self.version.id
            elif isinstance(self.version, dict) and "id" in self.version:
                version = self.version["id"]
            elif isinstance(self.version, str):
                version = self.version

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "supplier": supplier_code,
            "parameters": parameters,
            "function": function_type,
            "type": "model",
            "version": version,
            "asset_id": self.id,
        }

    def get_parameters(self) -> List[dict]:
        """Get current parameter values for this model.

        Returns:
            List[dict]: List of parameter dictionaries with current values
        """
        parameters = []
        if self.params:
            for param in self.params:
                inp = self.inputs.get(param.name)
                param_value = inp.value if inp is not None else None
                if param_value is not None:
                    parameters.append(
                        {
                            "name": param.name,
                            "value": param_value,
                            "required": param.required,
                            "datatype": param.data_type,
                            "allow_multi": param.multiple_values,
                            "supports_variables": False,
                            "fixed": param.is_fixed,
                            "description": "",  # Default empty description
                        }
                    )
        return parameters

    @classmethod
    def _populate_filters(cls, params: dict) -> dict:
        """Override to handle model-specific filter structure."""
        # Call parent's _populate_filters to get basic pagination and common
        # filters
        filters = super()._populate_filters(params)

        # Handle 'q' parameter directly as per Swagger spec
        if params.get("q") is not None:
            filters["q"] = params["q"]

        # Handle saved filter
        if params.get("saved") is not None:
            filters["saved"] = params["saved"]

        # Handle host filter (maps to hostedBy in API)
        if params.get("host") is not None:
            filters["hosts"] = [params["host"]]

        # Handle developer filter (maps to developedBy in API)
        if params.get("developer") is not None:
            filters["developers"] = [params["developer"]]

        # Handle path prefix filter (e.g., "openai/gpt-4")
        if params.get("path") is not None:
            filters["path"] = params["path"]

        # functions - accept list of strings and convert to backend shape
        # Use v2 format: array of objects with "id" key (required by v2/models/paginate endpoint)
        if params.get("functions") is not None:
            functions_param = params["functions"]
            if isinstance(functions_param, list):
                filters["functions"] = [{"id": (f.value if hasattr(f, "value") else str(f))} for f in functions_param]
            else:
                value = functions_param.value if hasattr(functions_param, "value") else str(functions_param)
                filters["functions"] = [{"id": value}]

        # suppliers - should be array of strings
        if params.get("vendors") is not None:
            suppliers = params["vendors"]
            if isinstance(suppliers, list):
                filters["suppliers"] = [
                    (s.value["code"] if hasattr(s, "value") and isinstance(s.value, dict) else str(s))
                    for s in suppliers
                ]
            else:
                supplier_value = (
                    suppliers.value["code"]
                    if (hasattr(suppliers, "value") and isinstance(suppliers.value, dict))
                    else str(suppliers)
                )
                filters["suppliers"] = [supplier_value]

        # status - should be array of strings
        if params.get("status") is not None:
            status = params["status"]
            if isinstance(status, list):
                filters["status"] = [
                    (s.value if (hasattr(s, "value") and isinstance(s.value, str)) else str(s)) for s in status
                ]
            else:
                if hasattr(status, "value") and isinstance(status.value, str):
                    status_value = status.value
                else:
                    status_value = str(status)
                filters["status"] = [status_value]

        # source_languages - should be array of language codes
        if params.get("source_languages") is not None:
            source_langs = params["source_languages"]
            if isinstance(source_langs, list):
                filters["sourceLanguages"] = [
                    (lang.value if hasattr(lang, "value") and isinstance(lang.value, str) else str(lang))
                    for lang in source_langs
                ]
            else:
                lang_value = (
                    source_langs.value
                    if hasattr(source_langs, "value") and isinstance(source_langs.value, str)
                    else str(source_langs)
                )
                filters["sourceLanguages"] = [lang_value]

        # target_languages - should be array of language codes
        if params.get("target_languages") is not None:
            target_langs = params["target_languages"]
            if isinstance(target_langs, list):
                filters["targetLanguages"] = [
                    (lang.value if hasattr(lang, "value") and isinstance(lang.value, str) else str(lang))
                    for lang in target_langs
                ]
            else:
                lang_value = (
                    target_langs.value
                    if hasattr(target_langs, "value") and isinstance(target_langs.value, str)
                    else str(target_langs)
                )
                filters["targetLanguages"] = [lang_value]

        # is_finetunable - boolean filter
        # Note: v1 API uses "isFineTunable" (capital T), v2 API uses "isFinetunable" (lowercase t)
        if params.get("is_finetunable") is not None:
            filters["isFineTunable"] = params["is_finetunable"]

        # sort - should be array of objects with field and dir
        if params.get("sort_by") is not None or params.get("sort_order") is not None:
            sort_field = params.get("sort_by", "name")
            sort_order = params.get("sort_order", "asc")

            # Convert enum to string if needed
            if hasattr(sort_field, "value"):
                sort_field = sort_field.value

            # Convert sort order to integer
            if hasattr(sort_order, "value"):
                sort_dir = sort_order.value
            else:
                sort_dir = 1 if str(sort_order).lower() == "asc" else -1

            filters["sort"] = [{"field": str(sort_field), "dir": sort_dir}]
        else:
            # Always include empty sort array as backend requires it
            filters["sort"] = [{}]

        return filters
