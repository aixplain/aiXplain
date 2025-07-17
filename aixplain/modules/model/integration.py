import warnings
from aixplain.enums import Function, Supplier, FunctionType
from aixplain.modules.model import Model, ModelResponse
from aixplain.utils import config
from typing import Text, Optional, Union, Dict
from enum import Enum
from pydantic import BaseModel
import json

class AuthenticationSchema(Enum):
    BEARER_TOKEN = "BEARER_TOKEN"
    OAUTH1 = "OAUTH1"
    OAUTH2 = "OAUTH2"
    API_KEY = "API_KEY"
    BASIC = "BASIC"
    NO_AUTH = "NO_AUTH"
    
class BaseAuthenticationParams(BaseModel):
    name: Optional[Text] = None
    connector_id: Optional[Text] = None

def build_connector_params(**kwargs) -> BaseAuthenticationParams:
    name = kwargs.get("name")
    connector_id = kwargs.get("connector_id")
    return BaseAuthenticationParams(name=name, connector_id=connector_id)


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
        self.authentication_methods = json.loads([item for item in additional_info['attributes'] if item['name'] == 'auth_schemes'][0]['code'])


    def connect(self, authentication_schema: AuthenticationSchema, args: Optional[BaseAuthenticationParams] = None, data: Optional[Dict] = None, **kwargs) -> ModelResponse:
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
        if self.id == "686eb9cd26480723d0634d3e":
            return self.run({"data": kwargs.get("data")})

        if args is None:
            args = build_connector_params(**kwargs)

        if authentication_schema.value not in self.authentication_methods:
            raise ValueError(f"Authentication schema {authentication_schema.value} is not supported for this integration. Supported authentication methods: {self.authentication_methods}")
        
        if data is None:
            data = {}
            
        if authentication_schema not in [AuthenticationSchema.OAUTH2, AuthenticationSchema.OAUTH1, AuthenticationSchema.NO_AUTH]:
            required_params = json.loads([item for item in self.additional_info['attributes'] if item['name'] == authentication_schema.value + "-inputs"][0]['code'])
            required_params_names = [param['name'] for param in required_params]
            for param in required_params_names:
                if param not in data:
                    if len(required_params_names) == 1:
                        raise ValueError(f"Parameter '{param}' is required for {self.name} {authentication_schema.value} authentication. Please provide the parameter in the data dictionary.")
                    else:
                        raise ValueError(f"Parameters {required_params_names} are required for {self.name} {authentication_schema.value} authentication. Please provide the parameters in the data dictionary.")
            return self.run(
                {
                    "name": args.name,
                    "authScheme": authentication_schema.value,
                    "data": data,
                }
            )
        else:
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