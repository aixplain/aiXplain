from aixplain.enums import Function, Supplier, FunctionType
from aixplain.modules.model import Model, ModelResponse
from aixplain.utils import config
from typing import Text, Optional, Union, Dict
from enum import Enum


class AuthenticationSchema(Enum):
    BEARER = "BEARER_TOKEN"
    OAUTH = "OAUTH"
    OAUTH2 = "OAUTH2"


class ConnectorModel(Model):
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
        function_type: Optional[FunctionType] = FunctionType.SEARCH,
        **additional_info,
    ) -> None:
        """Connector Init

        Args:
            id (Text): ID of the Model
            name (Text): Name of the Model
            description (Text, optional): description of the model. Defaults to "".
            api_key (Text, optional): API key of the Model. Defaults to None.
            supplier (Union[Dict, Text, Supplier, int], optional): supplier of the asset. Defaults to "aiXplain".
            version (Text, optional): version of the model. Defaults to "1.0".
            function (Function, optional): model AI function. Defaults to None.
            is_subscribed (bool, optional): Is the user subscribed. Defaults to False.
            cost (Dict, optional): model price. Defaults to None.
            **additional_info: Any additional Model info to be saved
        """
        assert function_type == FunctionType.CONNECTOR, "Connector only supports connector function"
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

    def connect(self, authentication_schema: AuthenticationSchema, name: Optional[Text] = None, **kwargs) -> ModelResponse:
        """Connect to the connector

        Examples:
            - For Bearer Token Authentication:
                >>> connector.connect(AuthenticationSchema.BEARER, name="My Connection", token="1234567890")
            - For OAuth Authentication:
                >>> connector.connect(AuthenticationSchema.OAUTH, name="My Connection", client_id="1234567890", client_secret="1234567890")
            - For OAuth2 Authentication:
                >>> connector.connect(AuthenticationSchema.OAUTH2, name="My Connection")
                Make sure to click on the redirect url to complete the connection.

        Args:
            authentication_schema (AuthenticationSchema): Authentication schema
            name (Text, optional): Name of the connection. Defaults to None.
            **kwargs: Additional arguments

        Returns:
            id: Connection ID (retrieve it with ModelFactory.get(id))
        """

        if authentication_schema == AuthenticationSchema.BEARER:
            assert "token" in kwargs, "`token` is required for Bearer Token Authentication"
            token = kwargs.get("token")
            return self.run(
                {
                    "name": name,
                    "authScheme": authentication_schema.value,
                    "data": {
                        "token": token,
                    },
                }
            )
        elif authentication_schema == AuthenticationSchema.OAUTH:
            assert (
                "client_id" in kwargs and "client_secret" in kwargs
            ), "`client_id` and `client_secret` are required for OAuth Authentication"
            client_id = kwargs.get("client_id")
            client_secret = kwargs.get("client_secret")
            return self.run(
                {
                    "name": name,
                    "authScheme": authentication_schema.value,
                    "data": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                }
            )
        elif authentication_schema == AuthenticationSchema.OAUTH2:
            return self.run(
                {
                    "name": name,
                    "authScheme": authentication_schema.value,
                }
            )
        else:
            raise ValueError(f"Invalid authentication schema: {authentication_schema}")
