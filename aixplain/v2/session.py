"""Session module for aiXplain v2 SDK."""

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from dataclasses_json import dataclass_json, config

from .enums import AttachmentType
from .exceptions import APIError, ResourceError
from .resource import (
    BaseResource,
    GetResourceMixin,
    DeleteResourceMixin,
    BaseGetParams,
    BaseDeleteParams,
)

logger = logging.getLogger(__name__)


# Maps snake_case execution param keys to the camelCase the backend accepts.
# Kept in this module (not on Agent) so Session create/update — which carries
# the same params as legacy agent.run — uses the same normalization.
EXECUTION_PARAMS_MAP: Dict[str, str] = {
    "output_format": "outputFormat",
    "max_tokens": "maxTokens",
    "max_iterations": "maxIterations",
    "max_time": "maxTime",
    "expected_output": "expectedOutput",
}


def _normalize_execution_params(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Translate snake_case execution param keys to camelCase for the API."""
    if not params:
        return params
    return {EXECUTION_PARAMS_MAP.get(k, k): v for k, v in params.items()}


def _mime_to_attachment_type(mime_type: str) -> str:
    """Map a MIME type string to an AttachmentType value."""
    if not mime_type:
        return AttachmentType.UNKNOWN.value

    main_type = mime_type.split("/")[0] if "/" in mime_type else ""
    sub_type = mime_type.split("/")[1] if "/" in mime_type else ""

    # Code types
    code_subtypes = {
        "x-python",
        "javascript",
        "x-javascript",
        "typescript",
        "x-java-source",
        "x-c",
        "x-c++",
        "x-ruby",
        "x-go",
        "x-rust",
        "x-shellscript",
    }
    if sub_type in code_subtypes:
        return AttachmentType.CODE.value

    # Document types
    document_subtypes = {
        "pdf",
        "msword",
        "vnd.openxmlformats-officedocument.wordprocessingml.document",
        "vnd.ms-excel",
        "vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "vnd.ms-powerpoint",
        "vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    if sub_type in document_subtypes:
        return AttachmentType.DOCUMENT.value

    # Main type mapping
    type_map = {
        "image": AttachmentType.IMAGE.value,
        "video": AttachmentType.VIDEO.value,
        "audio": AttachmentType.AUDIO.value,
        "text": AttachmentType.TEXT.value,
    }
    if main_type in type_map:
        return type_map[main_type]

    return AttachmentType.UNKNOWN.value


def _parse_list_response(response: Any, item_type: str) -> list:
    """Parse a response that should be a bare JSON array.

    Args:
        response: The API response (should be a list).
        item_type: Description of items for error messages.

    Returns:
        The response as a list.

    Raises:
        ResourceError: If response is not a list.
    """
    if isinstance(response, list):
        return response
    raise ResourceError(
        f"Expected a list of {item_type} from the API, got {type(response).__name__}: {str(response)[:200]}"
    )


def _deserialize(cls, data: dict, description: str):
    """Safely deserialize a dict into a dataclass.

    Args:
        cls: The dataclass type with from_dict.
        data: The dict to deserialize.
        description: Description for error messages.

    Returns:
        The deserialized instance.

    Raises:
        ResourceError: If deserialization fails.
    """
    try:
        return cls.from_dict(data)
    except Exception as e:
        raise ResourceError(f"Failed to parse {description}: {e}. Response data: {str(data)[:200]}")


@dataclass_json
@dataclass
class SessionMessageAttachment:
    """Attachment on a session message."""

    url: str
    name: Optional[str] = None
    type: Optional[str] = None


@dataclass_json
@dataclass
class SessionMessage:
    """A message within a session (not a resource — all ops go through Session)."""

    id: str = ""
    session_id: str = field(default="", metadata=config(field_name="sessionId"))
    user_id: str = field(default="", metadata=config(field_name="userId"))
    agent_id: str = field(default="", metadata=config(field_name="agentId"))
    role: str = ""
    content: str = ""
    sequence: int = 0
    request_id: Optional[str] = field(default=None, metadata=config(field_name="requestId"))
    reaction: Optional[str] = None
    attachments: Optional[List[SessionMessageAttachment]] = None
    created_at: str = field(default="", metadata=config(field_name="createdAt"))


@dataclass_json
@dataclass
class ExecutionConfig:
    """Per-session execution configuration.

    Mirrors the run-time agent parameters historically passed to
    ``agent.run`` so that messages posted to a session execute the agent
    with the same configuration. The backend reads ``executionConfig``
    on session create/update and applies it when subsequent user
    messages trigger agent runs.

    Attributes:
        execution_params: Backend execution params (output format, max
            tokens, etc.). Both snake_case and camelCase keys are
            accepted; snake_case is normalized to camelCase on send.
        criteria: Free-form evaluation criteria sent to the agent.
        evolve: Evolution config as a JSON string (kept as a string to
            match the backend contract).
        identifier: Free-form identifier the backend can echo back on
            messages (e.g. for client-side correlation).
        run_response_generation: Whether the agent should run its final
            response-generation step.
    """

    execution_params: Optional[Dict[str, Any]] = field(default=None, metadata=config(field_name="executionParams"))
    criteria: Optional[str] = None
    evolve: Optional[str] = None
    identifier: Optional[str] = None
    run_response_generation: Optional[bool] = field(default=None, metadata=config(field_name="runResponseGeneration"))

    def to_api_dict(self) -> Dict[str, Any]:
        """Build the camelCase API payload, normalizing nested params.

        Only fields the caller set are included so the backend keeps
        existing values on partial updates.
        """
        out: Dict[str, Any] = {}
        normalized = _normalize_execution_params(self.execution_params)
        if normalized is not None:
            out["executionParams"] = normalized
        if self.criteria is not None:
            out["criteria"] = self.criteria
        if self.evolve is not None:
            out["evolve"] = self.evolve
        if self.identifier is not None:
            out["identifier"] = self.identifier
        if self.run_response_generation is not None:
            out["runResponseGeneration"] = self.run_response_generation
        return out

    @classmethod
    def coerce(cls, value: Any) -> Optional["ExecutionConfig"]:
        """Accept an ExecutionConfig, dict, or None and return a config or None."""
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls.from_dict(value)
        raise TypeError(f"execution_config must be ExecutionConfig, dict, or None; got {type(value).__name__}")


@dataclass_json
@dataclass(repr=False)
class Session(
    BaseResource,
    GetResourceMixin[BaseGetParams, "Session"],
    DeleteResourceMixin[BaseDeleteParams, "Session"],
):
    """Session resource for managing agent conversation sessions."""

    RESOURCE_PATH = "v1/sessions"

    user_id: str = field(default="", metadata=config(field_name="userId"))
    agent_id: str = field(default="", metadata=config(field_name="agentId"))
    name: Optional[str] = None
    status: str = "active"
    run_status: str = field(default="", metadata=config(field_name="runStatus"))
    message_count: int = field(default=0, metadata=config(field_name="messageCount"))
    last_message_preview: Optional[str] = field(default=None, metadata=config(field_name="lastMessagePreview"))
    last_message_at: Optional[str] = field(default=None, metadata=config(field_name="lastMessageAt"))
    created_at: str = field(default="", metadata=config(field_name="createdAt"))
    updated_at: str = field(default="", metadata=config(field_name="updatedAt"))
    execution_config: Optional[ExecutionConfig] = field(default=None, metadata=config(field_name="executionConfig"))

    def __post_init__(self) -> None:
        """Coerce dict execution_config (e.g. from kwargs) into ExecutionConfig."""
        if self.execution_config is not None and not isinstance(self.execution_config, ExecutionConfig):
            self.execution_config = ExecutionConfig.coerce(self.execution_config)

    def build_save_payload(self, **kwargs: Any) -> dict:
        """Build payload with only mutable fields."""
        payload: Dict[str, Any] = {}
        if self.agent_id:
            payload["agentId"] = self.agent_id
        if self.name is not None:
            payload["name"] = self.name
        if self.status:
            payload["status"] = self.status
        if self.execution_config is not None:
            payload["executionConfig"] = self.execution_config.to_api_dict()
        return payload

    @classmethod
    def list(
        cls,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List["Session"]:
        """List sessions with optional filters.

        Args:
            agent_id: Filter by agent ID.
            status: Filter by session status.
            user_id: Filter by user ID.

        Returns:
            List of Session instances.

        Raises:
            ResourceError: If the API response is not a list or
                deserialization fails.
            APIError: If the API request fails.
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for resource operations")

        params: Dict[str, str] = {}
        if agent_id is not None:
            params["agentId"] = agent_id
        if status is not None:
            params["status"] = status
        if user_id is not None:
            params["userId"] = user_id

        try:
            response = context.client.request("get", cls.RESOURCE_PATH, params=params)
        except APIError:
            raise
        except Exception as e:
            raise ResourceError(f"Failed to list sessions: {e}")

        items = _parse_list_response(response, "sessions")
        sessions = []
        for item in items:
            session = _deserialize(cls, item, "session")
            session.context = context
            session._update_saved_state()
            sessions.append(session)
        return sessions

    def messages(self) -> List[SessionMessage]:
        """Get all messages in this session.

        Returns:
            List of SessionMessage instances.

        Raises:
            ResourceError: If the API response is not a list or
                deserialization fails.
            APIError: If the API request fails.
        """
        self._ensure_valid_state()
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}/messages"

        try:
            response = self.context.client.request("get", path)
        except APIError:
            raise
        except Exception as e:
            raise ResourceError(f"Failed to list messages for session '{self.id}': {e}")

        items = _parse_list_response(response, "messages")
        return [_deserialize(SessionMessage, item, "session message") for item in items]

    def add_message(
        self,
        role: str,
        content: str,
        request_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        files: Optional[List[Union[str, Path]]] = None,
    ) -> SessionMessage:
        """Add a message to this session.

        Args:
            role: Message role ("user" or "assistant").
            content: Message content.
            request_id: Optional request ID to associate with the message.
            attachments: Pre-built attachment dicts with url, name, type keys.
            files: Local file paths to upload and attach.

        Returns:
            The created SessionMessage.

        Raises:
            ResourceError: If the operation fails.
            APIError: If the API request fails.
            FileUploadError: If a file upload fails.
        """
        self._ensure_valid_state()

        all_attachments = list(attachments) if attachments else []

        if files:
            from .upload_utils import FileUploader, MimeTypeDetector

            uploader = FileUploader(
                backend_url=self.context.backend_url,
                api_key=self.context.api_key,
            )
            for file_path in files:
                file_path_str = str(file_path)
                try:
                    download_url = uploader.upload(
                        file_path_str,
                        is_temp=True,
                        return_download_link=True,
                    )
                except Exception as e:
                    raise ResourceError(f"Failed to upload file '{file_path_str}' for session '{self.id}': {e}")
                mime_type = MimeTypeDetector.detect_mime_type(file_path_str)
                att_type = _mime_to_attachment_type(mime_type)
                all_attachments.append(
                    {
                        "url": download_url,
                        "name": os.path.basename(file_path_str),
                        "type": att_type,
                    }
                )

        payload: Dict[str, Any] = {"role": role, "content": content}
        if request_id is not None:
            payload["requestId"] = request_id
        if all_attachments:
            payload["attachments"] = all_attachments

        path = f"{self.RESOURCE_PATH}/{self.encoded_id}/messages"
        try:
            response = self.context.client.request("post", path, json=payload)
        except APIError:
            raise
        except Exception as e:
            raise ResourceError(f"Failed to add message to session '{self.id}': {e}")

        return _deserialize(SessionMessage, response, "session message")

    def get_message(self, message_id: str) -> SessionMessage:
        """Get a specific message by ID.

        Args:
            message_id: The message ID.

        Returns:
            The SessionMessage.

        Raises:
            ResourceError: If deserialization fails.
            APIError: If the API request fails (e.g., message not found).
        """
        self._ensure_valid_state()
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}/messages/{message_id}"
        try:
            response = self.context.client.request("get", path)
        except APIError:
            raise
        except Exception as e:
            raise ResourceError(f"Failed to get message '{message_id}' from session '{self.id}': {e}")
        return _deserialize(SessionMessage, response, "session message")

    def delete_message(self, message_id: str) -> None:
        """Delete a message from this session.

        Args:
            message_id: The message ID to delete.

        Raises:
            APIError: If the API request fails (e.g., message not found).
            ResourceError: If the session is in an invalid state.
        """
        self._ensure_valid_state()
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}/messages/{message_id}"
        try:
            self.context.client.request_raw("delete", path)
        except APIError:
            raise
        except Exception as e:
            raise ResourceError(f"Failed to delete message '{message_id}' from session '{self.id}': {e}")

    def react(self, message_id: str, reaction: Optional[str]) -> SessionMessage:
        """React to a message or clear a reaction.

        Only assistant messages can be reacted to.

        Args:
            message_id: The message ID to react to.
            reaction: "LIKE", "DISLIKE", or None to clear.

        Returns:
            The updated SessionMessage.

        Raises:
            APIError: If the API request fails (e.g., reacting to a
                non-assistant message).
            ResourceError: If deserialization fails.
        """
        self._ensure_valid_state()
        path = f"{self.RESOURCE_PATH}/{self.encoded_id}/messages/{message_id}/reaction"
        payload: Dict[str, Any] = {"reaction": reaction}
        try:
            response = self.context.client.request("post", path, json=payload)
        except APIError:
            raise
        except Exception as e:
            raise ResourceError(f"Failed to react to message '{message_id}' in session '{self.id}': {e}")
        return _deserialize(SessionMessage, response, "session message")
