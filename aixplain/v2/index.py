"""Index resource for the v2 API.

This module provides a typed, v2-native Index API — the v2 equivalent of the
legacy ``aixplain.factories.IndexFactory`` / ``aixplain.modules.model.IndexModel``.

It covers both planes of index management:

* **Control-plane** — :meth:`Index.create`, :meth:`Index.list`,
  :meth:`Index.get`, :meth:`Index.delete`.
* **Data-plane** — :meth:`Index.upsert`, :meth:`Index.search`,
  :meth:`Index.count`, :meth:`Index.get_record`, :meth:`Index.delete_record`,
  :meth:`Index.retrieve_records_with_filter`,
  :meth:`Index.delete_records_by_date`.

All operations return v2-native types (:class:`Index`, :class:`IndexResult`,
:class:`~aixplain.v2.resource.Page`, :class:`~aixplain.v2.resource.DeleteResult`)
and authenticate through the v2 :class:`~aixplain.v2.client.AixplainClient`, so
consumers never need to import the legacy ``aixplain.factories`` API.
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from dataclasses_json import config, dataclass_json
from pydantic import BaseModel, ConfigDict
from typing_extensions import Unpack

from .enums import DataType, EmbeddingModel, IndexStores, ResponseStatus, SplittingOptions
from .exceptions import ResourceError
from .resource import (
    BaseGetParams,
    BaseResource,
    BaseRunParams,
    DeleteResult,
    GetResourceMixin,
    Page,
    Result,
    RunnableResourceMixin,
)
from .upload_utils import upload_file

logger = logging.getLogger(__name__)

#: Model used to parse non-text files (PDF, DOCX, ...) into text during upsert.
DOCLING_MODEL_ID = "677bee6c6eb56331f9192a91"

#: Image file extensions recognised by the index data-plane.
_SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")


# ---------------------------------------------------------------------------
# Storage / file helpers (v2-native; patchable in tests)
# ---------------------------------------------------------------------------
def _is_supported_image_type(value: str) -> bool:
    """Return whether *value* points to a supported image format (by extension)."""
    return isinstance(value, str) and value.lower().endswith(_SUPPORTED_IMAGE_EXTENSIONS)


def _is_url(value: str) -> bool:
    """Return whether *value* looks like a URL (scheme-based, with a validator fallback)."""
    if not isinstance(value, str):
        return False
    if value.startswith(("s3://", "http://", "https://")):
        return True
    try:
        import validators

        return bool(validators.url(value))
    except Exception:
        return False


def _check_storage_type(value: Any) -> str:
    """Classify *value* as ``"file"`` (local path), ``"url"`` or ``"text"``."""
    try:
        if isinstance(value, (str, os.PathLike)) and os.path.exists(value) and os.path.isfile(value):
            return "file"
    except (TypeError, ValueError):
        pass
    if _is_url(value):
        return "url"
    return "text"


def _to_link(value: str) -> str:
    """Upload a local file and return its hosted link; pass through URLs/text unchanged."""
    if _check_storage_type(value) == "file":
        return upload_file(value)
    return value


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------
class Record:
    """A single record to be indexed.

    Attributes:
        value: The textual value of the record (for text records).
        value_type: The data type of the record (``DataType.TEXT`` or ``DataType.IMAGE``).
        id: The record identifier (a random UUID is generated when omitted).
        uri: The URI of the record (required for image records).
        attributes: Arbitrary metadata stored alongside the record.
    """

    def __init__(
        self,
        value: str = "",
        value_type: Union[DataType, str] = DataType.TEXT,
        id: Optional[str] = None,
        uri: str = "",
        attributes: Optional[dict] = None,
    ) -> None:
        """Initialize a new Record.

        Args:
            value: The textual value of the record.
            value_type: The data type of the value. Defaults to ``DataType.TEXT``.
            id: The record identifier. Defaults to a random UUID.
            uri: The URI of the record.
            attributes: Arbitrary metadata. Defaults to an empty dict.
        """
        self.value = value
        self.value_type = value_type
        self.id = id if id is not None else str(uuid4())
        self.uri = uri
        self.attributes = attributes if attributes is not None else {}

    def to_dict(self) -> dict:
        """Serialize the record into the backend ingest payload shape.

        Returns:
            dict: ``{data, dataType, document_id, uri, attributes}``.
        """
        return {
            "data": self.value,
            "dataType": str(self.value_type),
            "document_id": self.id,
            "uri": self.uri,
            "attributes": self.attributes,
        }

    def validate(self) -> None:
        """Validate the record and resolve local files to hosted links.

        Mirrors the legacy ``Record.validate`` semantics: text records require a
        value or a URI, image records require a URI, and local image files are
        uploaded and rewritten to their hosted link (with ``value_type`` promoted
        to ``DataType.IMAGE`` for recognised image files).

        Raises:
            AssertionError: If the value type is invalid or a required field is missing.
        """
        assert self.value_type in [DataType.TEXT, DataType.IMAGE], "Index Upsert Error: Invalid value type"
        if self.value_type == DataType.IMAGE:
            assert self.uri is not None and self.uri != "", "Index Upsert Error: URI is required for image records"
        else:
            assert (self.value is not None and self.value != "") or (self.uri is not None and self.uri != ""), (
                "Index Upsert Error: Either value or uri is required for text records"
            )

        storage_type = _check_storage_type(self.uri)
        if storage_type in ("file", "url"):
            if _is_supported_image_type(self.uri):
                self.value_type = DataType.IMAGE
            self.uri = _to_link(self.uri) if storage_type == "file" else self.uri


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
class IndexFilterOperator(Enum):
    """Comparison operators available for filtering index records."""

    EQUALS = "=="
    NOT_EQUALS = "!="
    CONTAINS = "in"
    NOT_CONTAINS = "not in"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUALS = ">="
    LESS_THAN_OR_EQUALS = "<="


class IndexFilter:
    """A filter used to search or retrieve records by field/value/operator.

    Attributes:
        field: The name of the field to filter on.
        value: The value to compare against.
        operator: The comparison operator (an :class:`IndexFilterOperator` or its string value).
    """

    def __init__(self, field: str, value: str, operator: Union[IndexFilterOperator, str]) -> None:
        """Initialize a new IndexFilter.

        Args:
            field: The name of the field to filter on.
            value: The value to compare against.
            operator: The comparison operator to use.
        """
        self.field = field
        self.value = value
        self.operator = operator

    def to_dict(self) -> dict:
        """Serialize the filter into its backend payload shape.

        Returns:
            dict: ``{field, value, operator}`` with the operator coerced to its string value.
        """
        return {
            "field": self.field,
            "value": self.value,
            "operator": self.operator.value if isinstance(self.operator, IndexFilterOperator) else self.operator,
        }


class Splitter:
    """Configuration for splitting documents into chunks before indexing.

    Attributes:
        split: Whether to split documents.
        split_by: The splitting unit (word, sentence, ...).
        split_length: The length of each chunk.
        split_overlap: The overlap between consecutive chunks.
    """

    def __init__(
        self,
        split: bool = False,
        split_by: SplittingOptions = SplittingOptions.WORD,
        split_length: int = 1,
        split_overlap: int = 0,
    ) -> None:
        """Initialize a new Splitter.

        Args:
            split: Whether to split documents. Defaults to ``False``.
            split_by: The splitting unit. Defaults to ``SplittingOptions.WORD``.
            split_length: The length of each chunk. Defaults to ``1``.
            split_overlap: The overlap between consecutive chunks. Defaults to ``0``.
        """
        self.split = split
        self.split_by = split_by
        self.split_length = split_length
        self.split_overlap = split_overlap


# ---------------------------------------------------------------------------
# Index parameters (control-plane creation)
# ---------------------------------------------------------------------------
class BaseIndexParams(BaseModel, ABC):
    """Abstract base for index creation parameters.

    Attributes:
        name: Name of the index collection.
        description: Optional description of the index collection.
    """

    model_config = ConfigDict(use_enum_values=True, validate_default=True)
    name: str
    description: Optional[str] = ""

    def to_dict(self) -> Dict:
        """Serialize the parameters for the create request (renaming ``name`` to ``data``)."""
        data = self.model_dump(exclude_none=True)
        data["data"] = data.pop("name")
        return data

    @property
    @abstractmethod
    def id(self) -> str:
        """The aiXplain store-model ID used to create this index type."""
        raise NotImplementedError


class BaseIndexParamsWithEmbeddingModel(BaseIndexParams, ABC):
    """Abstract base for index parameters that require an embedding model.

    Attributes:
        embedding_model: Embedding model to use. Defaults to ``EmbeddingModel.OPENAI_ADA002``.
        embedding_size: Optional embedding size.
    """

    embedding_model: Optional[Union[EmbeddingModel, str]] = EmbeddingModel.OPENAI_ADA002
    embedding_size: Optional[int] = None

    def to_dict(self) -> Dict:
        """Serialize the parameters, mapping embedding fields to the backend shape."""
        data = super().to_dict()
        data["model"] = data.pop("embedding_model")
        if data.get("embedding_size"):
            data["additional_params"] = {"embedding_size": data.pop("embedding_size")}
        return data


class AirParams(BaseIndexParamsWithEmbeddingModel):
    """Parameters for creating an AIR (aiXplain Index and Retrieval) index."""

    _id: str = IndexStores.AIR.get_model_id()

    @property
    def id(self) -> str:
        """The AIR store-model ID."""
        return self._id


class VectaraParams(BaseIndexParams):
    """Parameters for creating a Vectara index."""

    _id: str = IndexStores.VECTARA.get_model_id()

    @property
    def id(self) -> str:
        """The Vectara store-model ID."""
        return self._id


class ZeroEntropyParams(BaseIndexParams):
    """Parameters for creating a Zero Entropy index."""

    _id: str = IndexStores.ZERO_ENTROPY.get_model_id()

    @property
    def id(self) -> str:
        """The Zero Entropy store-model ID."""
        return self._id


class GraphRAGParams(BaseIndexParamsWithEmbeddingModel):
    """Parameters for creating a GraphRAG index.

    Attributes:
        llm: Optional ID of the LLM used for generation.
    """

    _id: str = IndexStores.GRAPHRAG.get_model_id()
    llm: Optional[str] = None

    @property
    def id(self) -> str:
        """The GraphRAG store-model ID."""
        return self._id


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
@dataclass_json
@dataclass(repr=False)
class IndexResult(Result):
    """Result of an index data-plane operation.

    Extends :class:`~aixplain.v2.resource.Result` with the execution metadata the
    model-serving backend returns. ``status``/``completed`` carry defaults because
    some index actions (e.g. ``count``) return only ``status`` and ``data``.
    """

    status: str = ResponseStatus.SUCCESS.value
    completed: bool = True
    details: Optional[Any] = None
    run_time: Optional[float] = field(default=None, metadata=config(field_name="runTime"))
    used_credits: Optional[float] = field(default=None, metadata=config(field_name="usedCredits"))
    usage: Optional[Any] = None


class IndexRunParams(BaseRunParams):
    """Run parameters for index data-plane actions (``timeout``, ``wait_time``)."""

    pass


# ---------------------------------------------------------------------------
# Index resource
# ---------------------------------------------------------------------------
@dataclass_json
@dataclass(repr=False)
class Index(
    BaseResource,
    GetResourceMixin[BaseGetParams, "Index"],
    RunnableResourceMixin[IndexRunParams, IndexResult],
):
    """A vector index collection, with control-plane and data-plane operations.

    Use the client-bound resource (``client.Index``) for all operations::

        from aixplain.v2 import Aixplain
        from aixplain.v2.index import AirParams, Record, IndexFilter, IndexFilterOperator

        client = Aixplain()
        index = client.Index.create(params=AirParams(name="docs", description="My docs"))
        index.upsert([Record(value="Hello, world!")])
        results = index.search("hello")
        index.delete()
    """

    RESOURCE_PATH = "v2/models"
    RESPONSE_CLASS = IndexResult

    # Index-specific informational fields (populated from the model metadata).
    version: Optional[Any] = None
    embedding_model: Optional[str] = None
    embedding_size: Optional[int] = None
    collection_type: Optional[str] = None

    # -- enum / type re-exports for convenient access via the resource --------
    EmbeddingModel = EmbeddingModel
    IndexStores = IndexStores

    # ------------------------------------------------------------------
    # Run plumbing
    # ------------------------------------------------------------------
    def build_run_url(self, **kwargs: Unpack[IndexRunParams]) -> str:
        """Build the model-execution URL for data-plane actions."""
        self._ensure_valid_state()
        return f"{self.context.model_url}/{self.id}"

    def _run_index_action(
        self,
        action_payload: dict,
        *,
        timeout: int = 300,
        wait_time: float = 0.5,
    ) -> IndexResult:
        """Execute an index action payload and poll until completion.

        Args:
            action_payload: The ``{"action": ..., "data": ...}`` payload to POST.
            timeout: Maximum time in seconds to wait for async completion.
            wait_time: Initial interval in seconds between poll attempts.

        Returns:
            IndexResult: The (completed) result of the action.

        Raises:
            OperationFailedError: If the backend reports a ``FAILED`` status.
        """
        self._ensure_valid_state()
        run_url = self.build_run_url()
        response = self.context.client.request("post", run_url, json=action_payload)
        result = self.handle_run_response(response)
        if result.url and not result.completed:
            result = self.sync_poll(result.url, timeout=timeout, wait_time=wait_time)
        return result

    # ------------------------------------------------------------------
    # Control-plane
    # ------------------------------------------------------------------
    @classmethod
    def create(
        cls,
        name: Optional[str] = None,
        description: Optional[str] = None,
        embedding_model: Union[EmbeddingModel, str] = EmbeddingModel.OPENAI_ADA002,
        params: Optional[BaseIndexParams] = None,
        timeout: int = 300,
    ) -> "Index":
        """Create a new index collection.

        Prefer passing a typed ``params`` object (``AirParams``, ``VectaraParams``,
        ``GraphRAGParams``, ``ZeroEntropyParams``). The legacy
        ``name``/``description``/``embedding_model`` form creates an AIR index.

        Args:
            name: Name of the index (legacy form; mutually exclusive with ``params``).
            description: Description of the index (legacy form).
            embedding_model: Embedding model for the legacy form.
            params: Typed index parameters (recommended).
            timeout: Maximum time in seconds to wait for creation.

        Returns:
            Index: The created index collection.

        Raises:
            AssertionError: If the arguments are inconsistent.
            ResourceError: If creation fails.
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for index creation")

        if params is not None:
            assert name is None and description is None, (
                "Index creation: name and description must not be provided when params is provided"
            )
            store_model_id = params.id
            data = params.to_dict()
        else:
            assert name is not None and description is not None and embedding_model is not None, (
                "Index creation: name, description, and embedding_model must be provided when params is not"
            )
            model_value = embedding_model.value if isinstance(embedding_model, Enum) else embedding_model
            data = {"data": name, "description": description, "model": model_value}
            store_model_id = IndexStores.AIR.get_model_id()

        # Run the store model with the create payload; the new collection ID is
        # returned in the response ``data`` field.
        store = cls(id=store_model_id)
        result = store._run_index_action(data, timeout=timeout)
        if result.status == ResponseStatus.SUCCESS and result.data:
            return cls.get(result.data)

        error_message = result.error_message or "An error occurred while creating the index collection."
        raise ResourceError(f"Index creation failed: {error_message}")

    @classmethod
    def get(cls: type["Index"], id: str, **kwargs: Unpack[BaseGetParams]) -> "Index":
        """Get an index collection by ID.

        Args:
            id: The index (model) ID.
            **kwargs: Additional get parameters.

        Returns:
            Index: The retrieved index collection.
        """
        return super().get(id, **kwargs)

    @classmethod
    def list(
        cls,
        query: str = "",
        page_number: int = 0,
        page_size: int = 20,
    ) -> Page["Index"]:
        """List available index collections (function = ``SEARCH``).

        Useful to resolve a collection by name (filter the returned page by
        ``index.name``).

        Args:
            query: Optional search query to filter indexes by name.
            page_number: Page number for pagination (0-indexed).
            page_size: Number of results per page.

        Returns:
            Page[Index]: A page of index collections.
        """
        context = getattr(cls, "context", None)
        if context is None:
            raise ResourceError("Context is required for resource listing")

        filters = {
            "q": query or "",
            "pageNumber": page_number,
            "pageSize": page_size,
            "functions": ["search"],
        }
        headers = {"Authorization": f"Token {context.api_key}"}
        response = context.client.request("post", "sdk/models/paginate", json=filters, headers=headers)

        items = response.get("items")
        if items is None:
            items = response.get("results", [])

        results: List["Index"] = []
        for item in items:
            try:
                obj = cls.from_dict(item)
            except Exception as e:  # pragma: no cover - defensive
                logger.warning("Skipping item during Index deserialization: %s", e)
                continue
            setattr(obj, "context", context)
            obj._update_saved_state()
            results.append(obj)

        total = response.get("total", len(results))
        page_total = response.get("pageTotal", len(results))
        return Page(results=results, page_number=page_number, page_total=page_total, total=total)

    def delete(self, **kwargs: Any) -> DeleteResult:
        """Delete this index collection.

        Returns:
            DeleteResult: The result of the delete operation.

        Raises:
            APIError: If the deletion fails (e.g. the index does not exist or the
                caller is not the owner).
        """
        self._ensure_valid_state()
        deleted_id = self.id
        url = f"sdk/models/{self.encoded_id}"
        headers = {
            "Authorization": f"Token {self.context.api_key}",
            "Content-Type": "application/json",
        }
        self.context.client.request_raw("delete", url, headers=headers)

        # Mark the resource as deleted.
        self.id = None
        self._deleted = True

        return DeleteResult(status=ResponseStatus.SUCCESS.value, completed=True, deleted_id=deleted_id)

    # ------------------------------------------------------------------
    # Data-plane
    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[List[IndexFilter]] = None,
        score_threshold: float = 0.0,
        timeout: int = 300,
    ) -> IndexResult:
        """Search for records in the index.

        Args:
            query: The query text, or a file path / URL for image search.
            top_k: Number of results to return.
            filters: Optional list of :class:`IndexFilter` to apply.
            score_threshold: Minimum score threshold for results.
            timeout: Maximum time in seconds to wait for completion.

        Returns:
            IndexResult: The search result (``result.data`` holds the matches).
        """
        filters = filters or []
        uri, value_type = "", "text"
        storage_type = _check_storage_type(query)
        if storage_type in ("file", "url"):
            uri = _to_link(query)
            query = ""
            value_type = "image"

        data = {
            "action": "search",
            "data": query or uri,
            "dataType": value_type,
            "filters": [index_filter.to_dict() for index_filter in filters],
            "payload": {
                "uri": uri,
                "value_type": value_type,
                "top_k": top_k,
                "score_threshold": score_threshold,
            },
        }
        return self._run_index_action(data, timeout=timeout)

    def upsert(
        self,
        documents: Union[List[Record], str],
        splitter: Optional[Splitter] = None,
        timeout: int = 300,
    ) -> IndexResult:
        """Upsert records into the index.

        Args:
            documents: A list of :class:`Record` objects, or a file path to ingest.
            splitter: Optional :class:`Splitter` controlling chunking.
            timeout: Maximum time in seconds to wait for completion.

        Returns:
            IndexResult: The upsert result; on success ``result.data`` holds the
            list of ingested record payloads.
        """
        if isinstance(documents, str):
            documents = [self.prepare_record_from_file(documents)]

        for doc in documents:
            doc.validate()

        payloads = [doc.to_dict() for doc in documents]
        data: Dict[str, Any] = {"action": "ingest", "data": payloads}
        if splitter and splitter.split:
            data["additional_params"] = {
                "splitter": {
                    "split": splitter.split,
                    "split_by": splitter.split_by,
                    "split_length": splitter.split_length,
                    "split_overlap": splitter.split_overlap,
                }
            }

        result = self._run_index_action(data, timeout=timeout)
        if result.status == ResponseStatus.SUCCESS:
            result.data = payloads
        return result

    def count(self, timeout: int = 300) -> int:
        """Return the total number of records in the index."""
        result = self._run_index_action({"action": "count", "data": ""}, timeout=timeout)
        return int(result.data)

    def get_record(self, record_id: str, timeout: int = 300) -> IndexResult:
        """Retrieve a single record by ID."""
        return self._run_index_action({"action": "get_document", "data": record_id}, timeout=timeout)

    def delete_record(self, record_id: str, timeout: int = 300) -> IndexResult:
        """Delete a single record by ID."""
        return self._run_index_action({"action": "delete", "data": record_id}, timeout=timeout)

    def retrieve_records_with_filter(self, index_filter: IndexFilter, timeout: int = 300) -> IndexResult:
        """Retrieve records matching the given filter."""
        return self._run_index_action(
            {"action": "retrieve_by_filter", "data": index_filter.to_dict()}, timeout=timeout
        )

    def delete_records_by_date(self, date: float, timeout: int = 300) -> IndexResult:
        """Delete records matching the given date (timestamp)."""
        return self._run_index_action({"action": "delete_by_date", "data": date}, timeout=timeout)

    # ------------------------------------------------------------------
    # File ingestion helpers
    # ------------------------------------------------------------------
    def prepare_record_from_file(self, file_path: str, file_id: Optional[str] = None) -> Record:
        """Parse a file into a text :class:`Record`.

        Args:
            file_path: Path to the file to ingest.
            file_id: Optional record ID; a unique ID is generated when omitted.

        Returns:
            Record: A text record holding the parsed file content.
        """
        text = self.parse_file(file_path)
        file_name = os.path.basename(file_path)
        if not file_id:
            file_id = file_name + "_" + str(uuid4())
        return Record(value=text, value_type=DataType.TEXT, id=file_id, attributes={"file_name": file_name})

    def parse_file(self, file_path: str, timeout: int = 300) -> str:
        """Parse a file into text (plain read for ``.txt``, Docling otherwise).

        Args:
            file_path: Path to the file to parse.
            timeout: Maximum time in seconds to wait for Docling parsing.

        Returns:
            str: The parsed text content.

        Raises:
            ResourceError: If the file does not exist or parsing fails.
        """
        if not os.path.exists(file_path):
            raise ResourceError(f"File {file_path} does not exist")

        if file_path.endswith(".txt"):
            with open(file_path, "r") as handle:
                return handle.read()

        try:
            link = _to_link(file_path)
            run_url = f"{self.context.model_url}/{DOCLING_MODEL_ID}"
            response = self.context.client.request("post", run_url, json={"data": link})
            result = self.handle_run_response(response)
            if result.url and not result.completed:
                result = self.sync_poll(result.url, timeout=timeout)
            return result.data
        except Exception as e:
            raise ResourceError(f"Failed to parse file: {e}")
