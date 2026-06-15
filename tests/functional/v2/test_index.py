"""Functional (live) tests for the v2 Index API (ENG-3148).

These exercise the full control-plane + data-plane against a real backend using
the module-scoped ``client`` fixture (which skips when no API key is set).

The final test demonstrates the ENG-3148 acceptance criterion: an
``AiXplainVectorStore``-style wrapper implemented with **only** ``aixplain.v2``
(no ``aixplain.factories`` import).
"""

import time

import pytest

from aixplain.v2.index import (
    AirParams,
    Index,
    IndexFilter,
    IndexFilterOperator,
    Record,
)
from aixplain.v2.enums import EmbeddingModel, ResponseStatus


def _unique_name(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def _wait_until(fn, predicate, attempts: int = 12, delay: float = 2.0):
    """Poll ``fn`` until ``predicate`` is satisfied (tolerates indexing delay)."""
    value = None
    for _ in range(attempts):
        value = fn()
        if predicate(value):
            return value
        time.sleep(delay)
    return value


@pytest.fixture()
def index(client):
    """Create a fresh AIR index and delete it after the test."""
    created = client.Index.create(
        params=AirParams(
            name=_unique_name("eng3148-fn"),
            description="ENG-3148 functional test",
            embedding_model=EmbeddingModel.MULTILINGUAL_E5_LARGE,
        )
    )
    try:
        yield created
    finally:
        if created.id:
            try:
                created.delete()
            except Exception:
                pass


def test_index_create_returns_v2_index(client, index):
    """create() returns a v2-native Index instance with an ID and name."""
    assert isinstance(index, Index)
    assert index.id
    assert index.name


def test_index_data_plane_lifecycle(client, index):
    """upsert -> count -> search -> filter -> retrieve -> get_record -> delete_record."""
    records = [
        Record(value="The Eiffel Tower is in Paris, France.", id="doc-1", attributes={"category": "landmark"}),
        Record(value="The Colosseum is in Rome, Italy.", id="doc-2", attributes={"category": "landmark"}),
        Record(value="Python is a popular programming language.", id="doc-3", attributes={"category": "tech"}),
    ]
    up = index.upsert(records)
    assert up.status == ResponseStatus.SUCCESS
    assert isinstance(up.data, list) and len(up.data) == 3

    count = _wait_until(index.count, lambda c: c and c >= 3)
    assert count >= 3

    res = _wait_until(
        lambda: index.search("where is the eiffel tower", top_k=3),
        lambda r: r.status == ResponseStatus.SUCCESS and r.details,
    )
    assert res.status == ResponseStatus.SUCCESS
    # Structured matches are returned in ``details``.
    assert isinstance(res.details, list) and len(res.details) > 0

    filtered = index.search(
        "language",
        top_k=5,
        filters=[IndexFilter("category", "tech", IndexFilterOperator.EQUALS)],
    )
    assert filtered.status == ResponseStatus.SUCCESS

    retrieved = index.retrieve_records_with_filter(
        IndexFilter("category", "landmark", IndexFilterOperator.EQUALS)
    )
    assert retrieved.status == ResponseStatus.SUCCESS

    got = index.get_record("doc-1")
    assert got.status == ResponseStatus.SUCCESS

    deleted = index.delete_record("doc-3")
    assert deleted.status == ResponseStatus.SUCCESS


def test_index_list_resolves_by_name(client, index):
    """list() returns Index instances and resolves the collection by name."""
    # Allow the freshly created index to propagate to the catalog.
    match = _wait_until(
        lambda: [ix for ix in client.Index.list(query=index.name, page_size=50) if ix.name == index.name],
        lambda m: bool(m),
    )
    assert match, f"index {index.name!r} not resolvable by name"
    assert isinstance(match[0], Index)
    assert match[0].id == index.id


def test_index_create_validation(client):
    """create() rejects inconsistent argument combinations (mirrors legacy)."""
    with pytest.raises(AssertionError):
        client.Index.create(
            name="x",
            description="x",
            params=AirParams(name="x", description="x"),
        )
    with pytest.raises(AssertionError):
        client.Index.create(name="x")  # missing description


def test_v2_only_vector_store(client):
    """ENG-3148 acceptance: an AiXplainVectorStore built with only aixplain.v2.

    This mirrors the agents-framework ``AiXplainVectorStore`` surface, proving it
    can be implemented without the legacy ``aixplain.factories`` API.
    """

    class AiXplainVectorStore:
        """Minimal vector store backed entirely by the v2 Index API."""

        def __init__(self, aixplain_client, *, name, description="", embedding_model=EmbeddingModel.MULTILINGUAL_E5_LARGE):
            self._client = aixplain_client
            # Resolve an existing collection by name, else create one.
            existing = [ix for ix in self._client.Index.list(query=name, page_size=50) if ix.name == name]
            if existing:
                self._index = self._client.Index.get(existing[0].id)
            else:
                self._index = self._client.Index.create(
                    params=AirParams(name=name, description=description, embedding_model=embedding_model)
                )

        @property
        def collection_id(self):
            return self._index.id

        def add(self, texts_with_ids):
            recs = [Record(value=t, id=i, attributes=a or {}) for (i, t, a) in texts_with_ids]
            return self._index.upsert(recs)

        def query(self, text, top_k=5, category=None):
            filters = [IndexFilter("category", category, IndexFilterOperator.EQUALS)] if category else []
            return self._index.search(text, top_k=top_k, filters=filters)

        def delete(self, record_id):
            return self._index.delete_record(record_id)

        def destroy(self):
            return self._index.delete()

    store = AiXplainVectorStore(client, name=_unique_name("eng3148-vs"), description="v2-only vector store")
    try:
        assert store.collection_id

        add_result = store.add(
            [
                ("a1", "Mount Everest is the tallest mountain on Earth.", {"category": "geo"}),
                ("a2", "The Pacific is the largest ocean.", {"category": "geo"}),
                ("a3", "Rust is a systems programming language.", {"category": "tech"}),
            ]
        )
        assert add_result.status == ResponseStatus.SUCCESS

        _wait_until(store._index.count, lambda c: c and c >= 3)

        result = _wait_until(
            lambda: store.query("what is the tallest mountain", top_k=3),
            lambda r: r.status == ResponseStatus.SUCCESS and r.details,
        )
        assert result.status == ResponseStatus.SUCCESS
        assert isinstance(result.details, list) and len(result.details) > 0

        tech = store.query("programming", category="tech")
        assert tech.status == ResponseStatus.SUCCESS
    finally:
        store.destroy()


def test_v2_index_module_has_no_legacy_factories_import():
    """The v2 Index module must not *import* the legacy aixplain.factories/modules API.

    Uses AST (not a substring scan) so docstring references to the legacy
    equivalents do not produce false positives.
    """
    import ast
    import inspect

    import aixplain.v2.index as index_module

    tree = ast.parse(inspect.getsource(index_module))
    legacy_imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            head = node.module.split(".")
            if head[:2] in (["aixplain", "factories"], ["aixplain", "modules"], ["aixplain", "v1"]):
                legacy_imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                head = alias.name.split(".")
                if head[:2] in (["aixplain", "factories"], ["aixplain", "modules"], ["aixplain", "v1"]):
                    legacy_imports.append(alias.name)

    assert not legacy_imports, f"v2 Index module imports legacy API: {legacy_imports}"
