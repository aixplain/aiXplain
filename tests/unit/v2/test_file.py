"""Unit tests for the v2 File asset (aixplain/v2/file.py)."""

from pathlib import Path

import pytest

from aixplain.v2.agent_evaluator import Dataset
from aixplain.v2.enums import FileType
from aixplain.v2.exceptions import FileUploadError, ValidationError
from aixplain.v2.file import DatasetPreview, File


def test_file_construction_detects_csv_type(tmp_path: Path) -> None:
    p = tmp_path / "handbook.csv"
    p.write_text("query\nhello\n", encoding="utf-8")
    f = File(str(p))
    assert f.file_path == str(p)
    assert f.file_type == FileType.CSV


def test_file_construction_detects_pdf_type(tmp_path: Path) -> None:
    p = tmp_path / "handbook.pdf"
    p.write_text("not a real pdf", encoding="utf-8")
    f = File(str(p))
    assert f.file_type == FileType.PDF


def test_file_construction_unknown_extension_is_other(tmp_path: Path) -> None:
    p = tmp_path / "handbook.xyz"
    p.write_text("data", encoding="utf-8")
    f = File(str(p))
    assert f.file_type == FileType.OTHER


def test_file_construction_missing_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileUploadError, match="not found"):
        File(str(missing))


def test_to_dataset_basic(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,reference\nq1,r1\nq2,\n", encoding="utf-8")
    ds = File(str(p)).to_dataset()
    assert isinstance(ds, Dataset)
    assert ds.name == "cases"
    assert len(ds.cases) == 2
    assert ds.cases[0].query == "q1" and ds.cases[0].reference == "r1"


def test_to_dataset_with_metadata_columns(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,id,note\na,1,hello\n", encoding="utf-8")
    ds = File(str(p)).to_dataset(name="custom", metadata_columns=["id", "note"])
    assert ds.name == "custom"
    assert ds.cases[0].metadata == {"id": 1, "note": "hello"}


def test_to_dataset_non_csv_raises(tmp_path: Path) -> None:
    p = tmp_path / "handbook.pdf"
    p.write_text("not a real pdf", encoding="utf-8")
    with pytest.raises(ValidationError, match="expected CSV"):
        File(str(p)).to_dataset()


def test_to_dataset_missing_query_column_raises(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("foo\nbar\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="query"):
        File(str(p)).to_dataset()


def test_to_dataset_empty_query_column_arg_raises(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query\nhello\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="query_column"):
        File(str(p)).to_dataset(query_column="")


def test_preview_dataset_basic(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,reference,context\nq1,r1,c1\nq2,r2,c2\n", encoding="utf-8")
    preview = File(str(p)).preview_dataset(metadata_columns=["context", "missing_col"])
    assert isinstance(preview, DatasetPreview)
    assert preview.num_rows == 2
    assert preview.columns == ["query", "reference", "context"]
    assert preview.query_column == "query"
    assert preview.reference_column == "reference"
    assert preview.metadata_columns_found == ["context"]
    assert preview.metadata_columns_missing == ["missing_col"]
    assert preview.other_columns == []


def test_preview_dataset_no_reference_column(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query,extra\nq1,e1\n", encoding="utf-8")
    preview = File(str(p)).preview_dataset()
    assert preview.reference_column is None
    assert preview.other_columns == ["extra"]


def test_preview_dataset_does_not_build_dataset(tmp_path: Path, monkeypatch) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("query\nq1\n", encoding="utf-8")

    def _fail(*args, **kwargs):
        raise AssertionError("Dataset.from_csv should not be called by preview_dataset")

    monkeypatch.setattr(Dataset, "from_csv", _fail)
    preview = File(str(p)).preview_dataset()
    assert preview.num_rows == 1


def test_preview_dataset_non_csv_raises(tmp_path: Path) -> None:
    p = tmp_path / "handbook.pdf"
    p.write_text("not a real pdf", encoding="utf-8")
    with pytest.raises(ValidationError, match="expected CSV"):
        File(str(p)).preview_dataset()


def test_preview_dataset_missing_query_column_raises(tmp_path: Path) -> None:
    p = tmp_path / "cases.csv"
    p.write_text("foo\nbar\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="query"):
        File(str(p)).preview_dataset()
