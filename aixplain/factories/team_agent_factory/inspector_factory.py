"""Factory for inspectors.

Example usage:

inspector = InspectorFactory.create_from_model(
    name="my_inspector",
    model_id="my_model",
    model_config={"prompt": "Check if the data is safe to use."},
    policy=InspectorPolicy.ADAPTIVE,
)
"""

import logging
from typing import Dict, Optional, Text
from urllib.parse import urljoin

from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.function import Function
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry


class InspectorFactory:
    """A class for creating an Inspector instance."""

    @classmethod
    def create_from_model(
        cls,
        name: Text,
        model_id: Text,
        model_config: Optional[Dict] = None,
        policy: InspectorPolicy = InspectorPolicy.ADAPTIVE,  # default: doing something dynamically
    ) -> Inspector:
        """Create a new inspector agent from an onboarded model.

        Args:
            name: Name of the inspector agent.
            model_id: ID of the underlying model to use for inspector.
            model_config: Configuration for the inspector. Defaults to None.
            policy: Action to take upon negative feedback (WARN/ABORT/ADAPTIVE). Defaults to ADAPTIVE.

        Returns:
            Inspector: The created inspector
        """
        # check if the model exists and is onboarded
        try:
            url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")

            headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
            logging.info(f"Start service for GET Model  - {url} - {headers}")
            r = _request_with_retry("get", url, headers=headers)
            resp = r.json()
        except Exception:
            raise ValueError(f"Inspector: Failed to get model with ID {model_id}")

        if 200 <= r.status_code < 300:
            if resp["status"] != AssetStatus.ONBOARDED:
                raise ValueError(f"Inspector: Model with ID {model_id} is not onboarded")
        else:
            error_message = f"Inspector: Failed to get model with ID {model_id} (status code = {r.status_code})\nError: {resp}"
            logging.error(error_message)
            raise Exception(error_message)

        # TODO: relax this constraint
        if resp["function"]["id"] != Function.GUARDRAILS.value:
            raise ValueError(
                f"Inspector: Only Guardrail models are supported at the moment. Model with ID {model_id} is a {resp['function']['id']} model"
            )

        return Inspector(
            name=name,
            model_id=model_id,
            model_params=model_config,
            policy=policy,
        )

    # TODO: add create method for basic inspector
