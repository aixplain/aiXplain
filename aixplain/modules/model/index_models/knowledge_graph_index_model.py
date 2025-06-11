from aiXplain.aixplain.modules.model.index_models.base_index_model import BaseIndexModel
from aixplain.enums import ResponseStatus
from typing import Text, Optional, Union, Dict, List, Any
from aixplain.modules.model.record import Record
from aixplain.modules.model.response import ModelResponse
from aixplain.enums import Function, Supplier, EmbeddingModel, IndexType


class KnowledgeGraphIndexModel(BaseIndexModel):
    supported_indices = ["graphrag"]

    def __init__(
        self,
        id: Text,
        name: Text,
        version: Text,
        description: Text = "",
        api_key: Optional[Text] = None,
        supplier: Union[Dict, Text, Supplier, int] = "aiXplain",
        function: Optional[Function] = None,
        is_subscribed: bool = False,
        cost: Optional[Dict] = None,
        embedding_model: Optional[EmbeddingModel] = None,
        llm: Optional[Text] = None,
        **additional_info,
    ):
        super().__init__(
            id,
            name,
            version,
            description,
            api_key,
            supplier,
            function,
            is_subscribed,
            cost,
            embedding_model,
            IndexType.KNOWLEDGE_GRAPH,
            **additional_info,
        )
        self.llm = llm

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["llm"] = self.llm
        return data

    def get_prompts(self) -> Dict[str, str]:
        data = {"action": "get_prompts", "data": ""}
        response = self.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            response.data = response.data
            return response
        raise Exception(f"Failed to get prompts: {response.error_message}")

    # Add documents to the storage. Later can run indexing process incrementally based on the new documents added.
    def add_documents(self, documents: List[Record]):
        # Validate documents
        for doc in documents:
            doc.validate()
        # Convert documents to payloads
        payloads = [doc.to_dict() for doc in documents]
        # Build payload
        data = {"action": "upload_documents", "data": payloads}
        response = self.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            response.data = documents
            return response
        raise Exception(f"Failed to add documents: {response.error_message}")

    # Run prompt auto tuning, while also adding new documents to the storage if provided.
    def auto_prompt_tune(self, documents: List[Record]) -> Dict[str, str]:
        # TODO: Check if any files are already uploaded. If none and documents is also None, then raise an error.
        self.add_documents(documents)
        # Build payload
        data = {"action": "auto_prompt_tune", "data": ""}
        # Run the indexing service
        response = self.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            return response.data
        raise Exception(f"Failed to upsert documents: {response.error_message}")

    def manual_prompt_tune(self, prompts: Dict[str, str]) -> Dict[str, str]:
        data = {"action": "manual_prompt_tune", "data": prompts}
        response = self.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            response.data = prompts
            return response
        raise Exception(f"Failed to prompt tune: {response.error_message}")

    # Start the indexing process based on files already uploaded.
    def graph_indexing(self):
        data = {"action": "ingest", "data": []}
        response = self.run(data=data)
        if response.status == ResponseStatus.SUCCESS:
            response.data = response.data
            return response
        raise Exception(f"Failed to run indexing: {response.error_message}")

    # Add current documents to the storage and start the indexing process.
    def upsert(self, documents: List[Record]) -> ModelResponse:
        """Upsert documents into the index

        Args:
            documents (List[Record]): List of documents to be upserted

        Returns:
            ModelResponse: Response from the indexing service

        Example:
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})])
        """
        self.add_documents(documents)
        return self.graph_indexing()
