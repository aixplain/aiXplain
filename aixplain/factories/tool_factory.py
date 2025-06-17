import warnings
from aixplain.enums import FunctionType
from aixplain.factories import ModelFactory
from aixplain.factories.model_factory.mixins import ModelGetterMixin, ModelListMixin
from aixplain.modules.model import Model
from aixplain.modules.model.index_model import IndexModel
from aixplain.modules.model.integration import Integration
from aixplain.modules.model.integration import BaseAuthenticationParams
from aixplain.factories.index_factory.utils import BaseIndexParams, AirParams, VectaraParams, ZeroEntropyParams, GraphRAGParams
from aixplain.enums.index_stores import IndexStores
from aixplain.modules.model.utility_model import BaseUtilityModelParams
from typing import Optional, Text, Union
from aixplain.enums import ResponseStatus
from aixplain.utils import config


class ToolFactory(ModelGetterMixin, ModelListMixin):
    backend_url = config.BACKEND_URL

    @classmethod
    def create(
        cls,
        integration: Optional[Union[Text, Model]] = None,
        params: Optional[Union[BaseUtilityModelParams, BaseIndexParams, BaseAuthenticationParams]] = None,
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
            return ModelFactory.create_utility_model(
                name=params.name,
                description=params.description,
                code=params.code,
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
            response = connector.connect(params)
            assert response.status == ResponseStatus.SUCCESS, f"Failed to connect to {connector.id} - {response.error_message}"
            connection = cls.get(response.data["id"])
            if "redirectURL" in response.data:
                warnings.warn(
                    f"Before using the tool, please visit the following URL to complete the connection: {response.data['redirectURL']}"
                )
            return connection
        else:
            raise ValueError("ToolFactory Error: Invalid params")
