import logging
from typing import Dict, Optional, Text
from urllib.parse import urljoin

from aixplain.enums.asset_status import AssetStatus
from aixplain.modules.model.guardrail_model import GuardrailModel, GuardrailPolicy
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry


class GuardrailFactory:
    """A static class for creating and managing Guardrail Models."""

    backend_url = config.BACKEND_URL

    @classmethod
    def create(
        cls,
        name: Text,
        description: Text,
        guard_id: Text,
        guard_config: Optional[Dict] = None,
        guard_instruction: Optional[Text] = None,
        policy: GuardrailPolicy = GuardrailPolicy.WARN,
        api_key: Optional[Text] = None,
        **additional_info,
    ) -> GuardrailModel:
        """Create a new Guardrail model.

        Args:
            name (Text): Name of the guardrail model
            description (Text): Description of the guardrail model
            guard_id (Text): ID of the underlying model to use for guardrail
            guard_config (Dict, optional): Configuration for the guardrail. Defaults to None.
            guard_instruction (Text, optional): Free text instruction for the guardrail. Defaults to None.
            policy (GuardrailPolicy, optional): Action to take if policy is violated. Defaults to WARN.
            api_key (Text, optional): API key for authentication. Defaults to None.
            **additional_info: Any additional model info to be saved

        Returns:
            GuardrailModel: The created guardrail model

        Raises:
            ValueError: If neither guard_config nor guard_instruction is provided
            ValueError: If guard_instruction is provided but guard_id is not a text generation model
        """
        if guard_config is None and guard_instruction is None:
            raise ValueError("Either guard_config or guard_instruction must be provided")

        if guard_instruction is not None:
            # Verify that guard_id is a text generation model
            url = urljoin(cls.backend_url, f"sdk/models/{guard_id}")
            headers = {"x-api-key": api_key, "Content-Type": "application/json"}
            try:
                r = _request_with_retry("get", url, headers=headers)
                if r.status_code != 200:
                    raise ValueError(f"Model with ID {guard_id} not found")
                model_info = r.json()
                if model_info.get("function") != "text_generation":
                    raise ValueError("guard_id must be a text generation model when using guard_instruction")

                guard_config = {"instruction": guard_instruction, "model_id": guard_id}
            except Exception as e:
                raise ValueError(f"Error verifying model: {str(e)}")

        url = urljoin(cls.backend_url, "sdk/guardrails")
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "name": name,
            "description": description,
            "guardId": guard_id,
            "guardConfig": guard_config,
            "policy": policy.value,
            "status": AssetStatus.DRAFT.value,
            **additional_info,
        }

        try:
            logging.info(f"Start service for POST Guardrail Model - {url} - {headers} - {payload}")
            r = _request_with_retry("post", url, headers=headers, json=payload)
            response = r.json()
        except Exception as e:
            message = f"Guardrail Model Creation Error: {e}"
            logging.error(message)
            raise Exception(f"{message}")

        if not 200 <= r.status_code < 300:
            message = f"Guardrail Model Creation Error: {response}"
            logging.error(message)
            raise Exception(f"{message}")

        return GuardrailModel(
            id=response["id"],
            name=name,
            description=description,
            guard_id=guard_id,
            guard_config=guard_config,
            policy=policy,
            api_key=api_key,
            **additional_info,
        )

    @classmethod
    def get(cls, guardrail_id: Text, api_key: Optional[Text] = None) -> GuardrailModel:
        """Get a guardrail model by ID.

        Args:
            guardrail_id (Text): ID of the guardrail model to retrieve
            api_key (Text, optional): API key for authentication. Defaults to None.

        Returns:
            GuardrailModel: The retrieved guardrail model

        Raises:
            Exception: If the guardrail model cannot be retrieved
        """
        url = urljoin(cls.backend_url, f"sdk/guardrails/{guardrail_id}")
        headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        try:
            logging.info(f"Start service for GET Guardrail Model - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            response = r.json()
        except Exception as e:
            message = f"Guardrail Model Get Error: {e}"
            logging.error(message)
            raise Exception(f"{message}")

        if not 200 <= r.status_code < 300:
            message = f"Guardrail Model Get Error: {response}"
            logging.error(message)
            raise Exception(f"{message}")

        return GuardrailModel(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            guard_id=response["guardId"],
            guard_config=response["guardConfig"],
            policy=GuardrailPolicy(response["policy"]),
            api_key=api_key,
            status=AssetStatus(response["status"]),
        )
