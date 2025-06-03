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
from typing import Dict, Optional, Text, Union
from urllib.parse import urljoin

from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.function import Function
from aixplain.factories.model_factory.utils import create_model_from_response
from aixplain.modules.model import Model
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy, InspectorAuto
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry


INSPECTOR_SUPPORTED_FUNCTIONS = [Function.GUARDRAILS, Function.TEXT_GENERATION]


class InspectorFactory:
    """A class for creating an Inspector instance."""

    @classmethod
    def create_from_model(
        cls,
        name: Text,
        model: Union[Text, Model],
        model_config: Optional[Dict] = None,
        policy: InspectorPolicy = InspectorPolicy.ADAPTIVE,  # default: doing something dynamically
    ) -> Inspector:
        """Create a new inspector agent from an onboarded model.

        Args:
            name: Name of the inspector agent.
            model: Model or model ID to use for inspector.
            model_config: Configuration for the inspector. Defaults to None.
            policy: Action to take upon negative feedback (WARN/ABORT/ADAPTIVE). Defaults to ADAPTIVE.

        Returns:
            Inspector: The created inspector
        """
        # fetch model if model ID is provided
        if isinstance(model, Text):
            model_id = model
            try:
                url = urljoin(config.BACKEND_URL, f"sdk/models/{model_id}")

                headers = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
                logging.info(f"Start service for GET Model  - {url} - {headers}")
                r = _request_with_retry("get", url, headers=headers)
                resp = r.json()
            except Exception:
                raise ValueError(f"Inspector: Failed to get model with ID {model_id}")

            if 200 <= r.status_code < 300:
                model = create_model_from_response(resp)
            else:
                error_message = (
                    f"Inspector: Failed to get model with ID {model_id} (status code = {r.status_code})\nError: {resp}"
                )
                logging.error(error_message)
                raise Exception(error_message)
        else:
            model_id = model.id

        # check if the model is onboarded
        if model.status != AssetStatus.ONBOARDED:
            raise ValueError(f"Inspector: Model with ID {model_id} is not onboarded")

        # TODO: relax this constraint
        if model.function not in INSPECTOR_SUPPORTED_FUNCTIONS:
            raise ValueError(
                f"Inspector: Only {', '.join([f.value for f in INSPECTOR_SUPPORTED_FUNCTIONS])} models are supported at the moment. Model with ID {model_id} is a {model.function} model"
            )

        return Inspector(
            name=name,
            model_id=model_id,
            model_params=model_config,
            policy=policy,
        )

    @classmethod
    def create_auto(
        cls,
        auto: InspectorAuto,
        name: Optional[Text] = None,
        policy: InspectorPolicy = InspectorPolicy.ADAPTIVE,
    ) -> Inspector:
        """Create a new inspector agent from an automatically configured inspector.

        Args:
            auto: The automatically configured inspector.
            policy: Action to take upon negative feedback (WARN/ABORT/ADAPTIVE). Defaults to ADAPTIVE.

        Returns:
            Inspector: The created inspector.
        """
        return Inspector(
            name=name or auto.get_name(),
            auto=auto,
            policy=policy,
        )
