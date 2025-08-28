"""Factory module for creating and configuring inspector agents.

This module provides functionality for creating inspector agents that can validate
and monitor team agent operations. Inspectors can be created from existing models
or using automatic configurations.

WARNING: This feature is currently in private beta.

Example:
    Create an inspector from a model with adaptive policy::

        inspector = InspectorFactory.create_from_model(
            name="my_inspector",
            model_id="my_model",
            model_config={"prompt": "Check if the data is safe to use."},
            policy=InspectorPolicy.ADAPTIVE,
        )

Note:
    Currently only supports GUARDRAILS and TEXT_GENERATION models as inspectors.
"""

import logging
from typing import Dict, Optional, Text, Union, Callable
from urllib.parse import urljoin

from aixplain.enums.asset_status import AssetStatus
from aixplain.enums.function import Function
from aixplain.factories.model_factory.utils import create_model_from_response
from aixplain.modules.model import Model
from aixplain.modules.team_agent.inspector import Inspector, InspectorPolicy, InspectorAuto
from aixplain.utils import config
from aixplain.utils.file_utils import _request_with_retry


INSPECTOR_SUPPORTED_FUNCTIONS = [Function.GUARDRAILS, Function.TEXT_GENERATION, Function.UTILITIES]


class InspectorFactory:
    """Factory class for creating and configuring inspector agents.

    This class provides methods for creating inspector agents either from existing
    models or using automatic configurations. Inspectors are used to validate and
    monitor team agent operations, providing feedback and enforcing policies.
    """

    @classmethod
    def create_from_model(
        cls,
        name: Text,
        model: Union[Text, Model],
        model_config: Optional[Dict] = None,
        policy: Union[InspectorPolicy, Callable] = InspectorPolicy.ADAPTIVE,  # default: doing something dynamically
    ) -> Inspector:
        """Create a new inspector agent from an onboarded model.

        This method creates an inspector agent using an existing model that has been
        onboarded to the platform. The model must be of a supported function type
        (currently GUARDRAILS or TEXT_GENERATION).

        Args:
            name (Text): Name of the inspector agent.
            model (Union[Text, Model]): Either a Model instance or model ID string
                to use for the inspector.
            model_config (Optional[Dict], optional): Configuration parameters for
                the inspector model (e.g., prompts, thresholds). Defaults to None.
            policy: Action to take upon negative feedback (WARN/ABORT/ADAPTIVE)
                or a callable function. If callable, must have name "process_response",
                arguments "model_response" and "input_content" (both strings), and
                return InspectorAction. Defaults to ADAPTIVE.

        Returns:
            Inspector: Created and configured inspector agent.

        Raises:
            ValueError: If:
                - Model ID is invalid
                - Model is not onboarded
                - Model function is not supported
            Exception: If model retrieval fails
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
        policy: Union[InspectorPolicy, Callable] = InspectorPolicy.ADAPTIVE,
    ) -> Inspector:
        """Create a new inspector agent using automatic configuration.

        This method creates an inspector agent using a pre-configured InspectorAuto
        instance, which provides automatic inspection capabilities without requiring
        a specific model.

        Args:
            auto (InspectorAuto): Pre-configured automatic inspector instance.
            name (Optional[Text], optional): Name for the inspector. If not provided,
                uses the name from the auto configuration. Defaults to None.
            policy: Action to take upon negative feedback (WARN/ABORT/ADAPTIVE)
                or a callable function. If callable, must have name "process_response",
                arguments "model_response" and "input_content" (both strings), and
                return InspectorAction. Defaults to ADAPTIVE.

        Returns:
            Inspector: Created and configured inspector agent using automatic
            inspection capabilities.
        """
        return Inspector(
            name=name or auto.get_name(),
            auto=auto,
            policy=policy,
        )
