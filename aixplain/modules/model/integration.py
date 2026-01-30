"""Integration module for aiXplain SDK.

This module provides classes and utilities for working with external service
integrations, including authentication schemes and connection management.
"""

import warnings
from aixplain.enums import Function, Supplier, FunctionType
from aixplain.modules.model import Model, ModelResponse
from aixplain.utils import config
from typing import Text, Optional, Union, Dict
from enum import Enum
from pydantic import BaseModel
import json


class AuthenticationSchema(Enum):
    """Enumeration of supported authentication schemes for integrations.

    This enum defines the various authentication methods that can be used
    when connecting to external services through integrations.

    Attributes:
        BEARER_TOKEN (str): Bearer token authentication scheme.
        OAUTH1 (str): OAuth 1.0 authentication scheme.
        OAUTH2 (str): OAuth 2.0 authentication scheme.
        API_KEY (str): API key authentication scheme.
        BASIC (str): Basic authentication scheme (username/password).
        NO_AUTH (str): No authentication required.
    """

    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH1 = "OAUTH1"
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    BASIC = "BASIC"
    NO_AUTH = "NO_AUTH"


class BaseAuthenticationParams(BaseModel):
    """Base model for authentication parameters used in integrations.

    This class defines the common parameters that are used across different
    authentication schemes when connecting to external services.

    Attributes:
        name (Optional[Text]): Optional name for the connection. Defaults to None.
        connector_id (Optional[Text]): Optional ID of the connector. Defaults to None.
    """

    name: Optional[Text] = None
    description: Optional[Text] = None
    connector_id: Optional[Text] = None


def build_connector_params(**kwargs) -> BaseAuthenticationParams:
    """Build authentication parameters for a connector from keyword arguments.

    This function creates a BaseAuthenticationParams instance from the provided
    keyword arguments, extracting the name and connector_id if present.

    Args:
        **kwargs: Arbitrary keyword arguments. Supported keys:
            - name (Optional[Text]): Name for the connection
            - description (Optional[Text]): Description for the connection
            - connector_id (Optional[Text]): ID of the connector

    Returns:
        BaseAuthenticationParams: An instance containing the extracted parameters.

    Example:
        >>> params = build_connector_params(name="My Connection", description="My Connection Description", connector_id="123")
        >>> print(params.name)
        'My Connection'
    """
    name = kwargs.get("name")
    description = kwargs.get("description")
    connector_id = kwargs.get("connector_id")
    return BaseAuthenticationParams(name=name, description=description, connector_id=connector_id)


class Integration(Model):
    """Integration class for managing external service integrations.

    This class extends the Model class to provide functionality for connecting
    to and interacting with external services through integrations.
    """

    def __init__(
        self,
        id: Text,
        name: Text,
        description: Text = "",
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        version: Optional[Text] = None,
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        function_type: Optional[FunctionType] = FunctionType.INTEGRATION,
        **additional_info,
    ) -> None:
        """Initialize a new Integration instance.

        Args:
            id (Text): ID of the Integration.
            name (Text): Name of the Integration.
            description (Text, optional): Description of the Integration. Defaults to "".
            api_key (Text, optional): API key for the Integration. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): Supplier of the Integration. Defaults to "aiXplain".
            version (Text, optional): Version of the Integration. Defaults to "1.0".
            function (Function, optional): Function of the Integration. Defaults to None.
            is_subscribed (bool, optional): Whether the user is subscribed. Defaults to False.
            cost (Dict, optional): Cost of the Integration. Defaults to None.
            function_type (FunctionType, optional): Type of the function. Must be FunctionType.INTEGRATION.
                Defaults to FunctionType.INTEGRATION.
            **additional_info: Any additional Integration info to be saved.

        Raises:
            AssertionError: If function_type is not FunctionType.INTEGRATION.
        """
        assert function_type == FunctionType.INTEGRATION, "Integration only supports connector function"
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
            function_type=function_type,
            **additional_info,
        )
        self.url = config.MODELS_RUN_URL
        self.backend_url = config.BACKEND_URL
        self.authentication_methods = json.loads(
            [item for item in additional_info["attributes"] if item["name"] == "auth_schemes"][0]["code"]
        )

    def connect(
        self,
        authentication_schema: Optional[AuthenticationSchema] = None,
        args: Optional[BaseAuthenticationParams] = None,
        data: Optional[Union[Dict, Text]] = None,
        **kwargs,
    ) -> ModelResponse:
        """Connect to the integration using the specified authentication scheme.

        This method establishes a connection to the integration service using the provided
        authentication method and credentials. The required parameters vary depending on
        the authentication scheme being used.

        Args:
            authentication_schema (Optional[AuthenticationSchema]): The authentication scheme to use
                (e.g., BEARER_TOKEN, OAUTH1, OAUTH2, API_KEY, BASIC, NO_AUTH). Optional for MCP connections.
            args (Optional[BaseAuthenticationParams], optional): Common connection parameters.
                If not provided, will be built from kwargs. Defaults to None.
            data (Optional[Union[Dict, Text]], optional): Authentication-specific parameters required by
                the chosen authentication scheme. For MCP connections, can be a URL string.
                Defaults to None.
            **kwargs: Additional keyword arguments used to build BaseAuthenticationParams
                if args is not provided. Supported keys:
                - name (str): Name for the connection
                - connector_id (str): ID of the connector

        Returns:
            ModelResponse: A response object containing:
                - data (Dict): Contains connection details including:
                    - id (str): Connection ID (can be used with ModelFactory.get(id))
                    - redirectURL (str, optional): URL to complete OAuth authentication
                      (only for OAuth1/OAuth2)

        Raises:
            ValueError: If the authentication schema is not supported by this integration
                or if required parameters are missing from the data dictionary.

        Examples:
            Using Bearer Token authentication:
                >>> integration.connect(
                ...     AuthenticationSchema.BEARER_TOKEN,
                ...     data={"token": "1234567890"},
                ...     name="My Connection",
                ...     description="My Connection Description"
                ... )

            Using OAuth2 authentication:
                >>> response = integration.connect(
                ...     AuthenticationSchema.OAUTH2,
                ...     name="My Connection",
                ...     description="My Connection Description"
                ... )
                >>> # For OAuth2, you'll need to visit the redirectURL to complete auth
                >>> print(response.data.get("redirectURL"))

            Using API Key authentication:
                >>> integration.connect(
                ...     AuthenticationSchema.API_KEY,
                ...     data={"api_key": "your-api-key"},
                ...     name="My Connection",
                ...     description="My Connection Description"
                ... )

            Using MCP connection (no authentication schema required):
                >>> response = integration.connect(data="https://mcp.example.com/api/...")
        """
        if self.id == "686eb9cd26480723d0634d3e":
            # MCP connections: data can be a URL string or dict
            return self.run({"data": data} if data is not None else {"data": {}})

        # For non-MCP connections, authentication_schema is required
        if authentication_schema is None:
            raise ValueError(
                "authentication_schema is required for this integration. Please provide an AuthenticationSchema value."
            )

        if args is None:
            args = build_connector_params(**kwargs)

        if authentication_schema.value not in self.authentication_methods:
            raise ValueError(
                f"Authentication schema {authentication_schema.value} is not supported for this integration. Supported authentication methods: {self.authentication_methods}"
            )

        if data is None:
            data = {}

        if authentication_schema not in [
            AuthenticationSchema.OAUTH2,
            AuthenticationSchema.OAUTH1,
        ]:
            required_params = json.loads(
                [
                    item
                    for item in self.additional_info["attributes"]
                    if item["name"] == authentication_schema.value + "-inputs"
                ][0]["code"]
            )
            required_params_names = [param["name"] for param in required_params]
            for param in required_params_names:
                if param not in data:
                    if len(required_params_names) == 1:
                        raise ValueError(
                            f"Parameter '{param}' is required for {self.name} {authentication_schema.value} authentication. Please provide the parameter in the data dictionary."
                        )
                    else:
                        raise ValueError(
                            f"Parameters {required_params_names} are required for {self.name} {authentication_schema.value} authentication. Please provide the parameters in the data dictionary."
                        )
            return self.run(
                {
                    "name": args.name,
                    "description": args.description,
                    "authScheme": authentication_schema.value,
                    "data": data,
                }
            )
        else:
            response = self.run(
                {
                    "name": args.name,
                    "description": args.description,
                    "authScheme": authentication_schema.value,
                }
            )
            if "redirectURL" in response.data:
                warnings.warn(
                    f"Before using the tool, please visit the following URL to complete the connection: {response.data['redirectURL']}"
                )
            return response

    def __repr__(self):
        """Return a string representation of the Integration instance.

        Returns:
            str: A string in the format "Integration: <name> by <supplier> (id=<id>)".
                If supplier is a dictionary, uses supplier['name'], otherwise uses supplier directly.
        """
        try:
            return f"Integration: {self.name} by {self.supplier['name']} (id={self.id})"
        except Exception:
            return f"Integration: {self.name} by {self.supplier} (id={self.id})"
