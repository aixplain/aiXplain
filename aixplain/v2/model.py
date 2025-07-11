"""Model resource implementation for v2 API."""

from typing import Dict, Any, Optional, Union
from typing_extensions import Unpack, NotRequired

from .resource import BaseResource
from .mixins import (
    BaseRunnableResponse,
    BaseRunParams,
    RunnableMixin,
    ListResourceMixin,
    GetResourceMixin,
    CreateResourceMixin,
    DeleteResourceMixin,
    BareListParams,
    BareGetParams,
    BareCreateParams,
    BareDeleteParams,
)


class ModelRunParams(BaseRunParams):
    """Parameters for Model.run() method."""

    data: Union[str, Dict[str, Any]]
    name: NotRequired[str]
    parameters: NotRequired[Dict[str, Any]]
    stream: NotRequired[bool]


class ModelRunnableResponse(BaseRunnableResponse):
    """Response class optimized for Model resources.

    Provides Model-specific fields and behavior while maintaining compatibility
    with the legacy Model.run() response format.
    """

    def _parse_response(self, response_data: Dict[str, Any]) -> None:
        """Parse Model-specific response fields."""
        super()._parse_response(response_data)

        # Model-specific fields
        self.supplier_error: str = response_data.get("supplierError", "")
        self.model_id: Optional[str] = response_data.get("modelId")

        # Handle streaming responses
        self.streaming: bool = response_data.get("streaming", False)

    def _get_known_fields(self) -> set:
        """Include Model-specific fields in known fields."""
        base_fields = super()._get_known_fields()
        return base_fields | {"supplierError", "modelId", "streaming"}


class Model(
    BaseResource,
    ListResourceMixin[BareListParams, "Model"],
    GetResourceMixin[BareGetParams, "Model"],
    CreateResourceMixin[BareCreateParams, "Model"],
    DeleteResourceMixin[BareDeleteParams, "Model"],
    RunnableMixin[ModelRunParams],
):
    """Model resource class.

    Provides full CRUD operations plus run capabilities with Model-specific
    response handling.
    """

    RESOURCE_PATH = "sdk/models"
    RESPONSE_CLASS = ModelRunnableResponse

    def _build_run_payload(self, **kwargs: Unpack[ModelRunParams]) -> Dict[str, Any]:
        """Build Model-specific run payload."""
        data = kwargs.get("data")
        name = kwargs.get("name", "model-run")
        parameters = kwargs.get("parameters", {})
        stream = kwargs.get("stream", False)

        payload = {
            "data": data,
            "name": name,
        }

        # Add Model-specific parameters
        if parameters:
            payload["parameters"] = parameters

        if stream:
            payload["stream"] = stream

        return payload
