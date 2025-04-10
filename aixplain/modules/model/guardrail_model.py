"""
Guardrail Model Class
"""

import logging
import warnings
from aixplain.enums import Function, Supplier
from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model import Model
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry
from typing import Optional, Text, Dict, Union
from urllib.parse import urljoin


class GuardrailModel(Model):
    """Ready-to-use Guardrail Model.

    Note: Non-deployed guardrail models (status=DRAFT) will expire after 24 hours after creation.
    Use the .deploy() method to make the model permanent.

    Attributes:
        id (Text): ID of the Model
        name (Text): Name of the Model
        description (Text): description of the model. Defaults to "".
        model_config (Dict): configuration for the guardrail model
        policy (Enum): policy for the guardrail model
        api_key (Text, optional): API key of the Model. Defaults to None.
        supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
        version (Text, optional): version of the model. Defaults to "1.0".
        function (Function, optional): model AI function. Defaults to None.
        is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
        cost (Dict, optional): model price. Defaults to None.
        **additional_info: Any additional Model info to be saved
    """

    def __init__(
        self,
        id: Text,
        name: Optional[Text] = None,
        description: Optional[Text] = None,
        model_config: Optional[Dict] = None,
        policy: Optional[Enum] = None,
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        status: AssetStatus = AssetStatus.DRAFT,
        **additional_info,
    ) -> None:
        """Guardrail Model Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text): description of the model. Defaults to "".
            model_config (Dict): configuration for the guardrail model
            policy (Enum): policy for the guardrail model
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Function, optional): model AI function. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): model price. Defaults to None.
            **additional_info: Any additional Model info to be saved
        """
        super().__init__(
            id=id,
            name=name,
            description=description,
            supplier=supplier,
            version=version,
            cost=cost,
            function=function,
            is_subscribed=is_subscribed,
            api_key=api_key,
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.model_config = model_config or {}
        self.policy = policy
        if isinstance(status, str):
            try:
                status = AssetStatus(status)
            except Exception:
                status = AssetStatus.DRAFT
        self.status = status

        if status == AssetStatus.DRAFT:
            warnings.warn(
                "WARNING: Non-deployed guardrail models (status=DRAFT) will expire after 24 hours after creation. "
                "Use .deploy() method to make the model permanent.",
                UserWarning,
            )

    def validate(self):
        """Validate the Guardrail Model."""
        assert self.name and self.name.strip() != "", "Name is required"
        assert self.description and self.description.strip() != "", "Description is required"
        assert self.model_config is not None, "Model config is required"
        assert self.policy is not None, "Policy is required"

    def _model_exists(self):
        if self.id is None or self.id == "":
            return False
        url = urljoin(self.backend_url, f"sdk/models/{self.id}")
        headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}
        logging.info(f"Start service for GET Model  - {url} - {headers}")
        r = _request_with_retry("get", url, headers=headers)
        if r.status_code != 200:
            raise Exception()
        return True

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "modelConfig": self.model_config,
            "policy": self.policy.value if hasattr(self.policy, "value") else str(self.policy),
            "function": self.function.value if self.function else None,
            "status": self.status.value,
        }

    def update(self):
        """Update the Guardrail Model."""
        import warnings
        import inspect

        # Get the current call stack
        stack = inspect.stack()
        if len(stack) > 2 and stack[1].function != "save":
            warnings.warn(
                "update() is deprecated and will be removed in a future version. " "Please use save() instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.validate()
        url = urljoin(self.backend_url, f"sdk/guardrails/{self.id}")
        headers = {"x-api-key": f"{self.api_key}", "Content-Type": "application/json"}
        payload = self.to_dict()
        try:
            logging.info(f"Start service for PUT Guardrail Model - {url} - {headers} - {payload}")
            r = _request_with_retry("put", url, headers=headers, json=payload)
            response = r.json()
        except Exception as e:
            message = f"Guardrail Model Update Error: {e}"
            logging.error(message)
            raise Exception(f"{message}")

        if not 200 <= r.status_code < 300:
            message = f"Guardrail Model Update Error: {response}"
            logging.error(message)
            raise Exception(f"{message}")

    def save(self):
        """Save the Guardrail Model."""
        self.update()

    def delete(self):
        """Delete the Guardrail Model."""
        url = urljoin(self.backend_url, f"sdk/guardrails/{self.id}")
        headers = {"x-api-key": f"{self.api_key}", "Content-Type": "application/json"}
        try:
            logging.info(f"Start service for DELETE Guardrail Model  - {url} - {headers}")
            r = _request_with_retry("delete", url, headers=headers)
            response = r.json()
        except Exception:
            message = "Guardrail Model Deletion Error: Make sure the guardrail model exists and you are the owner."
            logging.error(message)
            raise Exception(f"{message}")

        if r.status_code != 200:
            message = f"Guardrail Model Deletion Error: {response}"
            logging.error(message)
            raise Exception(f"{message}")

    def deploy(self) -> None:
        assert self.status == AssetStatus.DRAFT, "Guardrail Model must be in draft status to be deployed."
        assert self.status != AssetStatus.ONBOARDED, "Guardrail Model is already deployed."
        self.status = AssetStatus.ONBOARDED
        self.update()
