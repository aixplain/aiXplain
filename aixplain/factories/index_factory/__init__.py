__author__ = "aiXplain"

"""
Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Abdul Basit Anees, Thiago Castro Ferreira, Zaina Abushaban
Date: December 26th 2024
Description:
    Index Factory Class
"""

from aixplain.modules.model.index_model import IndexModel
from aixplain.factories import ModelFactory
from aixplain.enums import (
    Function,
    ResponseStatus,
    SortBy,
    SortOrder,
    OwnershipType,
    Supplier,
    IndexStores,
    EmbeddingModel,
)
from typing import Text, Union, List, Tuple, Optional, TypeVar, Generic
from aixplain.factories.index_factory.utils import BaseIndexParams

T = TypeVar("T", bound=BaseIndexParams)


def validate_embedding_model(model_id: Union[EmbeddingModel, str]) -> bool:
    """Validate that a model is a text embedding model.

    Args:
        model_id (Union[EmbeddingModel, str]): The model ID or EmbeddingModel enum
            value to validate.

    Returns:
        bool: True if the model is a text embedding model, False otherwise.
    """
    model = ModelFactory.get(model_id)
    return model.function == Function.TEXT_EMBEDDING


class IndexFactory(ModelFactory, Generic[T]):
    """Factory class for creating and managing index collections.

    This class extends ModelFactory to provide specialized functionality for
    managing index collections, which are used for efficient data retrieval
    and searching. It supports various index types through the generic
    parameter T.

    Attributes:
        T (TypeVar): Type variable bound to BaseIndexParams, representing
            the specific index parameters type.
    """

    @classmethod
    def create(
        cls,
        name: Optional[Text] = None,
        description: Optional[Text] = None,
        embedding_model: Union[EmbeddingModel, str] = EmbeddingModel.OPENAI_ADA002,
        params: Optional[T] = None,
        **kwargs,
    ) -> IndexModel:
        """Create a new index collection for efficient data retrieval.

        This method supports two ways of creating an index:
        1. Using individual parameters (name, description, embedding_model) - Deprecated
        2. Using a params object of type T (recommended)

        Args:
            name (Optional[Text], optional): Name of the index collection.
                Deprecated, use params instead. Defaults to None.
            description (Optional[Text], optional): Description of the index collection.
                Deprecated, use params instead. Defaults to None.
            embedding_model (Union[EmbeddingModel, str], optional): Model to use for text embeddings.
                Deprecated, use params instead. Defaults to EmbeddingModel.OPENAI_ADA002.
            params (Optional[T], optional): Index parameters object. This is the
                recommended way to create an index. Defaults to None.
            **kwargs: Additional keyword arguments.

        Returns:
            IndexModel: Created index collection model.

        Raises:
            AssertionError: If neither params nor all legacy parameters are provided,
                or if both params and legacy parameters are provided.
            Exception: If index creation fails.
        """
        import warnings

        warnings.warn(
            "name, description, and embedding_model will be deprecated in the next release. Please use params instead.",
            DeprecationWarning,
        )

        model_id = IndexStores.AIR.get_model_id()
        if params is not None:
            model_id = params.id
            data = params.to_dict()
            assert (
                name is None and description is None
            ), "Index Factory Exception: name, description, and embedding_model must not be provided when params is provided"
        else:
            assert (
                name is not None and description is not None and embedding_model is not None
            ), "Index Factory Exception: name, description, and embedding_model must be provided when params is not"

            if validate_embedding_model(embedding_model):
                data = {
                    "data": name,
                    "description": description,
                    "model": embedding_model,
                }
        model = cls.get(model_id)

        response = model.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            model_id = response.data
            model = cls.get(model_id)
            return model

        error_message = f"Index Factory Exception: {response.error_message}"
        if response.error_message.strip() == "":
            error_message = "Index Factory Exception: An error occurred while creating the index collection."
        raise Exception(error_message)

    @classmethod
    def list(
        cls,
        query: Optional[Text] = "",
        suppliers: Optional[Union[Supplier, List[Supplier]]] = None,
        ownership: Optional[Tuple[OwnershipType, List[OwnershipType]]] = None,
        sort_by: Optional[SortBy] = None,
        sort_order: SortOrder = SortOrder.ASCENDING,
        page_number: int = 0,
        page_size: int = 20,
    ) -> List[IndexModel]:
        """List available index collections with optional filtering and sorting.

        Args:
            query (Optional[Text], optional): Search query to filter indexes.
                Defaults to "".
            suppliers (Optional[Union[Supplier, List[Supplier]]], optional): Filter by
                supplier(s). Defaults to None.
            ownership (Optional[Tuple[OwnershipType, List[OwnershipType]]], optional):
                Filter by ownership type. Defaults to None.
            sort_by (Optional[SortBy], optional): Field to sort results by.
                Defaults to None.
            sort_order (SortOrder, optional): Sort direction (ascending/descending).
                Defaults to SortOrder.ASCENDING.
            page_number (int, optional): Page number for pagination. Defaults to 0.
            page_size (int, optional): Number of results per page. Defaults to 20.

        Returns:
            List[IndexModel]: List of index models matching the specified criteria.
        """
        return super().list(
            function=Function.SEARCH,
            query=query,
            suppliers=suppliers,
            ownership=ownership,
            sort_by=sort_by,
            sort_order=sort_order,
            page_number=page_number,
            page_size=page_size,
        )
