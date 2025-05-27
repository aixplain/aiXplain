from aixplain.enums import Function, Supplier, FunctionType
from aixplain.modules.model import Model, ModelResponse
from aixplain.utils import config
from typing import Text, Optional, Union, Dict
from enum import Enum
from pydantic import BaseModel


class AuthenticationSchema(Enum):
    BEARER = "BEARER_TOKEN"
    OAUTH = "OAUTH"
    OAUTH2 = "OAUTH2"


class BaseAuthenticationParams(BaseModel):
    name: Optional[Text] = None
    authentication_schema: AuthenticationSchema = AuthenticationSchema.OAUTH2
    connector_id: Optional[Text] = None


class BearerAuthenticationParams(BaseAuthenticationParams):
    token: Text
    authentication_schema: AuthenticationSchema = AuthenticationSchema.BEARER


class OAuthAuthenticationParams(BaseAuthenticationParams):
    client_id: Text
    client_secret: Text
    authentication_schema: AuthenticationSchema = AuthenticationSchema.OAUTH


class OAuth2AuthenticationParams(BaseAuthenticationParams):
    authentication_schema: AuthenticationSchema = AuthenticationSchema.OAUTH2


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

    def connect(self, args: Optional[BaseAuthenticationParams] = None, **kwargs) -> ModelResponse:
        """Connect to the connector

        Examples:
            - For Bearer Token Authentication:
                >>> connector.connect(BearerAuthenticationSchema(name="My Connection", token="1234567890"))
                >>> connector.connect(BearerAuthenticationSchema(token="1234567890"))
                >>> connector.connect(token="1234567890")
            - For OAuth Authentication:
                >>> connector.connect(OAuthAuthenticationSchema(name="My Connection", client_id="1234567890", client_secret="1234567890"))
                >>> connector.connect(OAuthAuthenticationSchema(client_id="1234567890", client_secret="1234567890"))
                >>> connector.connect(client_id="1234567890", client_secret="1234567890")
            - For OAuth2 Authentication:
                >>> connector.connect(OAuth2AuthenticationSchema(name="My Connection"))
                >>> connector.connect()
                Make sure to click on the redirect url to complete the connection.

        Returns:
            id: Connection ID (retrieve it with ModelFactory.get(id))
            redirectUrl: Redirect URL to complete the connection (only for OAuth2)
        """
        if args is None:
            name = kwargs.get("name")
            token = kwargs.get("token")
            client_id = kwargs.get("client_id")
            client_secret = kwargs.get("client_secret")
            if token:
                args = BearerAuthenticationParams(name=name, token=token)
            elif client_id and client_secret:
                args = OAuthAuthenticationParams(name=name, client_id=client_id, client_secret=client_secret)
            else:
                args = OAuth2AuthenticationParams(name=name)

        authentication_schema = args.authentication_schema
        if authentication_schema == AuthenticationSchema.BEARER:
            return self.run(
                {
                    "name": args.name,
                    "authScheme": authentication_schema.value,
                    "data": {
                        "token": args.token,
                    },
                }
            )
        elif authentication_schema == AuthenticationSchema.OAUTH:
            return self.run(
                {
                    "name": args.name,
                    "authScheme": authentication_schema.value,
                    "data": {
                        "client_id": args.client_id,
                        "client_secret": args.client_secret,
                    },
                }
            )
        elif authentication_schema == AuthenticationSchema.OAUTH2:
            return self.run(
                {
                    "name": args.name,
                    "authScheme": authentication_schema.value,
                }
            )
