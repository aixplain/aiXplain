import warnings
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


def build_connector_params(**kwargs) -> BaseAuthenticationParams:
    name = kwargs.get("name")
    token = kwargs.get("token")
    client_id = kwargs.get("client_id")
    client_secret = kwargs.get("client_secret")
    connector_id = kwargs.get("connector_id")
    if token:
        args = BearerAuthenticationParams(name=name, token=token, connector_id=connector_id)
    elif client_id and client_secret:
        args = OAuthAuthenticationParams(name=name, client_id=client_id, client_secret=client_secret, connector_id=connector_id)
    else:
        args = OAuth2AuthenticationParams(name=name, connector_id=connector_id)
    return args


class Integration(Model):
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
        """Integration Init

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

    def connect(self, args: Optional[BaseAuthenticationParams] = None, **kwargs) -> ModelResponse:
        """Connect to the integration

        Examples:
            - For Bearer Token Authentication:
                >>> integration.connect(BearerAuthenticationSchema(name="My Connection", token="1234567890"))
                >>> integration.connect(BearerAuthenticationSchema(token="1234567890"))
                >>> integration.connect(token="1234567890")
            - For OAuth Authentication:
                >>> integration.connect(OAuthAuthenticationSchema(name="My Connection", client_id="1234567890", client_secret="1234567890"))
                >>> integration.connect(OAuthAuthenticationSchema(client_id="1234567890", client_secret="1234567890"))
                >>> integration.connect(client_id="1234567890", client_secret="1234567890")
            - For OAuth2 Authentication:
                >>> integration.connect(OAuth2AuthenticationSchema(name="My Connection"))
                >>> integration.connect()
                Make sure to click on the redirect url to complete the connection.

        Returns:
            id: Connection ID (retrieve it with ModelFactory.get(id))
            redirectUrl: Redirect URL to complete the connection (only for OAuth2)
        """
        if args is None:
            args = build_connector_params(**kwargs)

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
            response = self.run(
                {
                    "name": args.name,
                    "authScheme": authentication_schema.value,
                }
            )
            if "redirectURL" in response.data:
                warnings.warn(
                    f"Before using the tool, please visit the following URL to complete the connection: {response.data['redirectURL']}"
                )
            return response

    def __repr__(self):
        try:
            return f"Integration: {self.name} by {self.supplier['name']} (id={self.id})"
        except Exception:
            return f"Integration: {self.name} by {self.supplier} (id={self.id})"
