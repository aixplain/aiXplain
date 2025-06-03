from aixplain.modules.model.index_models.index_model import IndexModel, Splitter
from aixplain.enums import ResponseStatus
from typing import Text, Optional, Union, Dict, List, Any
from aixplain.modules.model.record import Record
from aixplain.modules.model.response import ModelResponse
from aixplain.enums import Function, Supplier, EmbeddingModel


class KnowledgeGraphIndexModel(IndexModel):
    supported_indices = ["graphrag"]

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
        embedding_model: Optional[EmbeddingModel] = None,
        llm: Optional[Text] = None,
        **additional_info,
    ):
        super().__init__(
            id, name, description, api_key, supplier, version, function, is_subscribed, cost, embedding_model, **additional_info
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
    def upsert(self, documents: List[Record], splitter: Optional[Splitter] = None) -> ModelResponse:
        """Upsert documents into the index

        Args:
            documents (List[Record]): List of documents to be upserted
            splitter (Splitter, optional): Splitter to be applied. Defaults to None.

        Returns:
            ModelResponse: Response from the indexing service

        Example:
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})])
            index_model.upsert([Record(value="Hello, world!", value_type="text", uri="", id="1", attributes={})], splitter=Splitter(split=True, split_by=SplittingOptions.WORD, split_length=1, split_overlap=0))
            Splitter in the above example is optional and can be used to split the documents into smaller chunks.
        """
        self.add_documents(documents)
        return self.graph_indexing()
