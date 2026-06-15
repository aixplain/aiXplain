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
from aixplain.v2.enums import DataType, EmbeddingModel, ResponseStatus


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


def _make_minimal_pdf(lines) -> bytes:
    """Build a tiny but valid single-page PDF (with /MediaBox) from text lines."""
    text = b"BT /F1 18 Tf 72 720 Td "
    text += b" ".join(b"(" + line.encode() + b") Tj 0 -26 Td" for line in lines)
    text += b" ET"
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(pdf))
        pdf += str(i).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref_pos = len(pdf)
    pdf += b"xref\n0 " + str(len(objs) + 1).encode() + b"\n0000000000 65535 f \n"
    for off in offsets:
        pdf += ("%010d 00000 n \n" % off).encode()
    pdf += b"trailer\n<< /Size " + str(len(objs) + 1).encode() + b" /Root 1 0 R >>\nstartxref\n"
    pdf += str(xref_pos).encode() + b"\n%%EOF"
    return pdf


def test_index_upsert_txt_file(client, index, tmp_path):
    """upsert(path) ingests a .txt file via the client-side plain-read path."""
    f = tmp_path / "quokka.txt"
    f.write_text("The quokka is a small marsupial native to Western Australia.")

    up = index.upsert(str(f))
    assert up.status == ResponseStatus.SUCCESS
    assert isinstance(up.data, list) and len(up.data) == 1
    assert "quokka" in up.data[0]["data"].lower()

    _wait_until(index.count, lambda c: c and c >= 1)
    res = _wait_until(
        lambda: index.search("where do quokkas live", top_k=2),
        lambda r: r.status == ResponseStatus.SUCCESS and r.details,
    )
    assert res.details and "quokka" in str(res.details).lower()


def test_index_upsert_pdf_file_via_docling(client, index, tmp_path):
    """upsert(path) ingests a .pdf by uploading and parsing it server-side (Docling)."""
    f = tmp_path / "photosynthesis.pdf"
    f.write_bytes(
        _make_minimal_pdf(
            [
                "Photosynthesis converts sunlight into chemical energy.",
                "Chlorophyll absorbs light and plants produce glucose and oxygen.",
            ]
        )
    )

    up = index.upsert(str(f))
    assert up.status == ResponseStatus.SUCCESS
    assert isinstance(up.data, list) and len(up.data) == 1
    assert "photosynth" in up.data[0]["data"].lower()

    _wait_until(index.count, lambda c: c and c >= 1)
    res = _wait_until(
        lambda: index.search("how do plants make energy from sunlight", top_k=2),
        lambda r: r.status == ResponseStatus.SUCCESS and r.details,
    )
    assert res.details
    assert any(
        kw in str(res.details).lower() for kw in ("photosynth", "chlorophyll", "glucose")
    )


def _make_png(path, base_rgb, block_rgb, w=96, h=96):
    """Write a valid PNG (solid base color with a contrasting centered block)."""
    import struct
    import zlib

    rows = bytearray()
    for y in range(h):
        rows.append(0)  # filter type 0
        for x in range(w):
            in_block = (w // 4 <= x < 3 * w // 4) and (h // 4 <= y < 3 * h // 4)
            r, g, b = block_rgb if in_block else base_rgb
            rows += bytes((r, g, b))

    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return str(path)


def test_index_image_upsert_and_text_search(client, tmp_path):
    """Multimodal index: upsert local image files, then query by text (CLIP cross-modal).

    Covers the image data path end-to-end: local image files are uploaded and stored
    as ``image`` records, and a text query searches the image vectors. (Image-*as-query*
    search is intentionally not asserted — it is not currently accepted by the backend
    and fails for the legacy SDK too.)
    """
    images = {
        "img-red": _make_png(tmp_path / "red.png", (200, 30, 30), (255, 255, 255)),
        "img-green": _make_png(tmp_path / "green.png", (30, 160, 60), (0, 0, 0)),
        "img-blue": _make_png(tmp_path / "blue.png", (30, 60, 200), (255, 255, 0)),
    }

    index = client.Index.create(
        params=AirParams(
            name=_unique_name("eng3148-img"),
            description="ENG-3148 image functional test",
            embedding_model=EmbeddingModel.JINA_CLIP_V2_MULTIMODAL,
        )
    )
    try:
        up = index.upsert(
            [Record(uri=path, value_type=DataType.IMAGE, id=rid, attributes={"id": rid}) for rid, path in images.items()]
        )
        assert up.status == ResponseStatus.SUCCESS
        assert isinstance(up.data, list) and len(up.data) == 3
        assert all(rec["dataType"] == "image" for rec in up.data)
        assert all(rec["uri"] for rec in up.data)  # local files were uploaded to a link

        count = _wait_until(index.count, lambda c: c and c >= 3)
        assert count >= 3

        res = _wait_until(
            lambda: index.search("a mostly red picture", top_k=3),
            lambda r: r.status == ResponseStatus.SUCCESS and r.details,
        )
        assert res.status == ResponseStatus.SUCCESS
        assert isinstance(res.details, list) and len(res.details) > 0
        # results reference the stored image records
        assert any(isinstance(d, dict) and d.get("document") for d in res.details)
    finally:
        index.delete()


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
