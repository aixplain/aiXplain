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
from aixplain.enums import Function, ResponseStatus, SortBy, SortOrder, OwnershipType, Supplier, IndexStores, EmbeddingModel
from typing import Text, Union, List, Tuple, Optional, TypeVar, Generic
from aixplain.factories.index_factory.utils import BaseIndexParams

T = TypeVar("T", bound=BaseIndexParams)


import os
from aixplain.utils.file_utils import _request_with_retry
from urllib.parse import urljoin

def validate_embedding_model(model_id) -> bool:
        model = ModelFactory.get(model_id)
        return model.function == Function.TEXT_EMBEDDING


def validate_embedding_model(model_id) -> bool:
    model = ModelFactory.get(model_id)
    return model.function == Function.TEXT_EMBEDDING


def validate_embedding_model(model_id) -> bool:
    model = ModelFactory.get(model_id)
    return model.function == Function.TEXT_EMBEDDING


class IndexFactory(ModelFactory, Generic[T]):
    @classmethod
    def create(
        cls,
        name: Optional[Text] = None,
        description: Optional[Text] = None,

        embedding_model: Union[EmbeddingModel, str] = EmbeddingModel.OPENAI_ADA002,

        params: Optional[T] = None,
        **kwargs,
    ) -> IndexModel:
        """Create a new index collection"""
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
        """List all indexes"""
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
