import warnings
from aixplain.enums import FunctionType
from aixplain.factories import ModelFactory
from aixplain.factories.model_factory.mixins import ModelGetterMixin, ModelListMixin
from aixplain.modules.model import Model
from aixplain.modules.model.index_model import IndexModel
from aixplain.modules.model.integration import Integration, AuthenticationSchema
from aixplain.modules.model.integration import BaseAuthenticationParams
from aixplain.factories.index_factory.utils import BaseIndexParams, AirParams, VectaraParams, ZeroEntropyParams, GraphRAGParams
from aixplain.enums.index_stores import IndexStores
from aixplain.modules.model.utility_model import BaseUtilityModelParams
from typing import Optional, Text, Union, Dict
from aixplain.enums import ResponseStatus
from aixplain.utils import config


class ToolFactory(ModelGetterMixin, ModelListMixin):
    """A factory class for creating and managing various types of tools including indexes, scripts, and connections.

    This class provides functionality to create and manage different types of tools:
    - Script models (utility models)
    - Search collections (index models)
    - Connectors (integration models)

    The factory inherits from ModelGetterMixin and ModelListMixin to provide model retrieval
    and listing capabilities.

    Attributes:
        backend_url: The URL endpoint for the backend API.
    """
    backend_url = config.BACKEND_URL


    @classmethod
    def recreate(
        cls,
        integration: Optional[Union[Text, Model]] = None,
        tool: Optional[Union[Text, Model]] = None,
        params: Optional[Union[BaseUtilityModelParams, BaseIndexParams, BaseAuthenticationParams]] = None,
        data: Optional[Dict] = None,
        **kwargs,
    ) -> Model:
        """Recreates a tool based on an existing tool's configuration.

        This method creates a new tool instance using the configuration of an existing tool.
        It's useful for creating copies or variations of existing tools.

        Args:
            integration (Optional[Union[Text, Model]], optional): The integration model or its ID. Defaults to None.
            tool (Optional[Union[Text, Model]], optional): The existing tool model or its ID to recreate from. Defaults to None.
            params (Optional[Union[BaseUtilityModelParams, BaseIndexParams, BaseAuthenticationParams]], optional): 
                Parameters for the new tool. Defaults to None.
            data (Optional[Dict], optional): Additional data for tool creation. Defaults to None.
            **kwargs: Additional keyword arguments passed to the tool creation process.

        Returns:
            Model: The newly created tool model.
        """
        if data is None: 
            data = {}
        data["assetId"] = tool.id if isinstance(tool, Model) else tool
        return ToolFactory.create(integration, params, AuthenticationSchema.NO_AUTH, data )
    
    @classmethod
    def create(
        cls,
        integration: Optional[Union[Text, Model]] = None,
        params: Optional[Union[BaseUtilityModelParams, BaseIndexParams, BaseAuthenticationParams]] = None,
        authentication_schema: Optional[AuthenticationSchema] = None,
        data: Optional[Dict] = None,
        **kwargs,
    ) -> Model:
        """Factory method to create indexes, script models and connections

        Examples:
            Create a script model (option 1):
                Option 1:
                    from aixplain.modules.model.utility_model import BaseUtilityModelParams

                    def add(a: int, b: int) -> int:
                        return a + b

                    params = BaseUtilityModelParams(
                        name="My Script Model",
                        description="My Script Model Description",
                        code=add
                    )
                    tool = ToolFactory.create(params=params)

                Option 2:
                    def add(a: int, b: int) -> int:
                        \"\"\"Add two numbers\"\"\"
                        return a + b

                    tool = ToolFactory.create(
                        name="My Script Model",
                        code=add
                    )

            Create a search collection:
                Option 1:
                    from aixplain.factories.index_factory.utils import AirParams

                    params = AirParams(
                        name="My Search Collection",
                        description="My Search Collection Description"
                    )
                    tool = ToolFactory.create(params=params)

                Option 2:
                    from aixplain.enums.index_stores import IndexStores

                    tool = ToolFactory.create(
                        integration=IndexStores.VECTARA.get_model_id(),
                        name="My Search Collection",
                        description="My Search Collection Description"
                    )

            Create a connector:
                Option 1:
                    from aixplain.modules.model.connector import BearerAuthenticationParams

                    params = BearerAuthenticationParams(
                        connector_id="my_connector_id",
                        token="my_token",
                        name="My Connection"
                    )
                    tool = ToolFactory.create(params=params)

                Option 2:
                    tool = ToolFactory.create(
                        integration="my_connector_id",
                        name="My Connection",
                        token="my_token"
                    )

        Args:
            params: The parameters for the tool
        Returns:
            The created tool
        """
        if params is None:
            integration_model = None
            if isinstance(integration, Text):
                integration_model = cls.get(integration)
            elif isinstance(integration, Model):
                integration_model = integration
                integration = integration_model.id

            assert (
                isinstance(integration_model, Integration)
                or isinstance(integration_model, IndexModel)
                or kwargs.get("code") is not None
            ), "Please provide the proper integration (ConnectorModel, IndexModel or UtilityModel code) or params to create a model tool."
            if isinstance(integration_model, Integration):
                from aixplain.modules.model.integration import build_connector_params

                kwargs["connector_id"] = integration_model.id
                params = build_connector_params(**kwargs)
            elif isinstance(integration_model, IndexModel):
                if IndexStores.AIR.get_model_id() == integration_model.id:
                    params = AirParams(**kwargs)
                elif IndexStores.VECTARA.get_model_id() == integration_model.id:
                    params = VectaraParams(**kwargs)
                elif IndexStores.ZERO_ENTROPY.get_model_id() == integration_model.id:
                    params = ZeroEntropyParams(**kwargs)
                elif IndexStores.GRAPHRAG.get_model_id() == integration_model.id:
                    params = GraphRAGParams(**kwargs)
                else:
                    raise ValueError(
                        f"ToolFactory Error: The index store '{integration_model.id} - {integration_model.name}' is not supported."
                    )
            else:
                params = BaseUtilityModelParams(**kwargs)

        if isinstance(params, BaseUtilityModelParams):
            return ModelFactory.create_script_connection_tool(
                name=params.name,
                description=params.description,
                code=params.code,
                function_name=kwargs.get("function_name", None),
            )
        elif isinstance(params, BaseIndexParams):
            from aixplain.factories import IndexFactory

            return IndexFactory.create(params=params)
        elif isinstance(params, BaseAuthenticationParams):
            assert params.connector_id is not None, "Please provide the ID of the service you want to connect to"
            connector = cls.get(params.connector_id)
            assert (
                connector.function_type == FunctionType.INTEGRATION
            ), f"The model you are trying to connect ({connector.id}) to is not a connector."
            
            assert authentication_schema is not None, "Please provide the authentication schema to use (authentication_schema parameter)"
            assert isinstance(authentication_schema, AuthenticationSchema), "authentication_schema must be an instance of AuthenticationSchema"
            
            auth_data = data if data is not None else {}
            if not auth_data:
                for key, value in kwargs.items():
                    if key not in ['name', 'connector_id']:
                        auth_data[key] = value
            
            response = connector.connect(authentication_schema, params, auth_data)
            assert response.status == ResponseStatus.SUCCESS, f"Failed to connect to {connector.id} - {response.error_message}"
            connection = cls.get(response.data["id"])
            if "redirectURL" in response.data:
                warnings.warn(
                    f"Before using the tool, please visit the following URL to complete the connection: {response.data['redirectURL']}"
                )
            return connection
        else:
            raise ValueError("ToolFactory Error: Invalid params")
