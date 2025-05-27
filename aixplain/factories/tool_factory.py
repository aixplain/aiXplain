from aixplain.enums import FunctionType
from aixplain.modules.model import Model
from aixplain.modules.model.connector import BaseAuthenticationParams
from aixplain.factories.index_factory.utils import BaseIndexParams
from aixplain.modules.model.utility_model import BaseScriptModelParams
from typing import Optional, Text, Union
from aixplain.enums import ResponseStatus


class ToolFactory:
    @classmethod
    def create(
        cls, params: Optional[Union[BaseScriptModelParams, BaseIndexParams, BaseAuthenticationParams]] = None, **kwargs
    ) -> Model:
        """Factory method to create indexes, script models and connections

        Examples:
            - Create a script model:

                >>> from aixplain.modules.model.utility_model import BaseScriptModelParams

                >>> def add(aaa: int, bbb: int) -> int: return aaa + bbb

                >>> params = BaseScriptModelParams(name="My Script Model", description="My Script Model Description", code=add)

                >>> tool = ToolFactory.create(params)
            - Create a search collection:

                >>> from aixplain.factories.index_factory.utils import AirParams

                >>> params = AirParams(name="My Search Collection", description="My Search Collection Description")

                >>> tool = ToolFactory.create(params)
            - Create a connector:

                >>> from aixplain.modules.model.connector import BearerAuthenticationParams

                >>> params = BearerAuthenticationParams(connector_id="my_connector_id", token="my_token", name="My Connection")

                >>> tool = ToolFactory.create(params)

        Args:
            params: The parameters for the tool
        Returns:
            The created tool
        """
        if isinstance(params, BaseScriptModelParams):
            from aixplain.factories import ModelFactory

            return ModelFactory.create_utility_model(
                name=params.name,
                description=params.description,
                code=params.code,
            )
        elif isinstance(params, BaseIndexParams):
            from aixplain.factories import IndexFactory

            return IndexFactory.create(params=params)
        elif isinstance(params, BaseAuthenticationParams):
            from aixplain.factories import ModelFactory

            assert params.connector_id is not None, "Please provide the ID of the service you want to connect to"
            connector = ModelFactory.get(params.connector_id)
            assert (
                connector.function_type == FunctionType.CONNECTOR
            ), f"The model you are trying to connect ({connector.id}) to is not a connector."
            response = connector.connect(params)
            assert response.status == ResponseStatus.SUCCESS, f"Failed to connect to {connector.id} - {response.error_message}"
            connection = ModelFactory.get(response.data["id"])
            return connection
        else:
            raise ValueError("Invalid params")
