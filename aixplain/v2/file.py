"""Simple Resource class for file handling and S3 uploads."""

import os
from typing import List, Optional, Sequence, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
import pandas as pd

from .resource import (
    BaseResource,
    GetResourceMixin,
    SearchResourceMixin,
    BaseGetParams,
    BaseSearchParams,
)
from .upload_utils import FileUploader, FileValidator
from .exceptions import FileUploadError, ValidationError
from .enums import FileType

if TYPE_CHECKING:
    from .agent_evaluator import Dataset


@dataclass_json
@dataclass
class ResourceGetParams:
    """Parameters for getting resources."""

    api_key: Optional[str] = None
    resource_path: Optional[str] = None


@dataclass_json
@dataclass(repr=False)
class Resource(BaseResource):
    """Simple resource class for file handling and S3 uploads.

    This class provides the basic functionality needed for the requirements:
    - File path handling
    - S3 upload via save()
    - URL access after upload
    """

    # File-related fields
    file_path: Optional[str] = field(default=None, metadata=config(field_name="filePath"))
    s3_url: Optional[str] = field(default=None, metadata=config(field_name="s3Url"))
    file_type: Optional[FileType] = field(default=None, metadata=config(field_name="fileType"))
    is_temp: bool = field(default=True, metadata=config(field_name="isTemp"))

    def __post_init__(self):
        """Initialize the resource."""
        # If file_path is provided, detect file type
        if self.file_path and not self.file_type:
            self.file_type = self._detect_file_type()

    def _detect_file_type(self) -> FileType:
        """Detect file type from file path."""
        if not self.file_path:
            return FileType.OTHER

        _, ext = os.path.splitext(self.file_path.lower())

        if ext == ".csv":
            return FileType.CSV
        elif ext == ".json":
            return FileType.JSON
        elif ext == ".txt":
            return FileType.TXT
        elif ext == ".pdf":
            return FileType.PDF
        elif ext in [".mp3", ".wav", ".flac", ".m4a"]:
            return FileType.AUDIO
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            return FileType.IMAGE
        elif ext in [".db", ".sqlite", ".sqlite3"]:
            return FileType.DATABASE
        else:
            return FileType.OTHER

    def build_save_payload(self, **kwargs) -> dict:
        """Build the payload for saving the resource."""
        payload = super().build_save_payload(**kwargs)

        # Add file-specific fields
        if self.file_path:
            payload["filePath"] = self.file_path
        if self.s3_url:
            payload["s3Url"] = self.s3_url
        if self.file_type:
            payload["fileType"] = self.file_type.value

        return payload

    def save(self, is_temp: Optional[bool] = None, **kwargs) -> "Resource":
        """Save the resource, uploading file to S3 if needed.

        Args:
            is_temp: Whether this is a temporary upload. If None, uses the resource's is_temp setting.
            **kwargs: Additional parameters for saving.
        """
        # Update is_temp if provided
        if is_temp is not None:
            self.is_temp = is_temp

        # If we have a file_path but no s3_url, upload the file first
        if self.file_path and not self.s3_url:
            self._upload_file()

        # For file resources, we don't save to backend - just upload to S3
        # The legacy system doesn't have a Resource management endpoint
        return self

    def _upload_file(self) -> None:
        """Upload the file to S3 and set the s3_url."""
        if not self.file_path or not os.path.exists(self.file_path):
            raise ValueError(f"File not found: {self.file_path}")

        # Use the file uploader with context's API key and backend URL
        uploader = FileUploader(
            api_key=self.context.client.team_api_key,
            backend_url=self.context.backend_url,
        )
        result = uploader.upload(self.file_path, is_temp=self.is_temp, return_download_link=True)

        # Set the presigned/public URL (result is the download link)
        self.s3_url = result

    @property
    def url(self) -> Optional[str]:
        """Get the presigned/public URL of the uploaded file."""
        return self.s3_url

    @classmethod
    def create_from_file(cls, file_path: str, is_temp: bool = True, **kwargs) -> "Resource":
        """Create a resource from a file path.

        Args:
            file_path: Path to the file to upload.
            is_temp: Whether this is a temporary upload (default: True).
            **kwargs: Additional parameters for initialization.
        """
        return cls(file_path=file_path, is_temp=is_temp, **kwargs)

    def __init__(self, file_path: Optional[str] = None, is_temp: bool = True, **kwargs):
        """Initialize the resource with file path.

        Args:
            file_path: Path to the file to upload.
            is_temp: Whether this is a temporary upload (default: True).
            **kwargs: Additional parameters for initialization.
        """
        super().__init__(**kwargs)
        if file_path:
            self.file_path = file_path
            if not self.file_type:
                self.file_type = self._detect_file_type()
        self.is_temp = is_temp


def _detect_file_type(file_path: str) -> FileType:
    """Detect file type from a file path's extension."""
    _, ext = os.path.splitext(file_path.lower())
    return {
        ".csv": FileType.CSV,
        ".json": FileType.JSON,
        ".txt": FileType.TXT,
        ".pdf": FileType.PDF,
        ".mp3": FileType.AUDIO,
        ".wav": FileType.AUDIO,
        ".flac": FileType.AUDIO,
        ".m4a": FileType.AUDIO,
        ".jpg": FileType.IMAGE,
        ".jpeg": FileType.IMAGE,
        ".png": FileType.IMAGE,
        ".gif": FileType.IMAGE,
        ".bmp": FileType.IMAGE,
        ".db": FileType.DATABASE,
        ".sqlite": FileType.DATABASE,
        ".sqlite3": FileType.DATABASE,
    }.get(ext, FileType.OTHER)


@dataclass
class DatasetPreview:
    """Report of what a CSV file contains for dataset conversion.

    Returned by :meth:`File.preview_dataset` after all validation has passed.
    """

    num_rows: int
    columns: List[str]
    query_column: str
    reference_column: Optional[str]
    metadata_columns_found: List[str]
    metadata_columns_missing: List[str]
    other_columns: List[str]


@dataclass_json
@dataclass(repr=False)
class File(BaseResource):
    """Local file reference asset.

    Wraps any local file path (``handbook = aix.File("handbook.pdf")``). This is a
    pure local reference - it does not upload or persist anywhere on its own. For
    CSV files, use :meth:`to_dataset` or :meth:`preview_dataset` to convert into
    (or inspect for conversion into) an evaluation :class:`~aixplain.v2.agent_evaluator.Dataset`.
    """

    file_path: Optional[str] = field(default=None, metadata=config(field_name="filePath"))
    file_type: Optional[FileType] = field(default=None, metadata=config(field_name="fileType"))

    def __init__(self, file_path: Optional[str] = None, **kwargs):
        """Initialize the file reference.

        Args:
            file_path: Path to the local file. Validated to exist immediately.
            **kwargs: Additional parameters forwarded to :class:`BaseResource`.
        """
        super().__init__(**kwargs)
        self.file_path = None
        self.file_type = None
        if file_path:
            FileValidator.validate_file_exists(file_path)
            self.file_path = file_path
            self.file_type = _detect_file_type(file_path)

    def _require_csv(self, query_column: str) -> None:
        """Validate that this File is ready to be read as a CSV for dataset conversion."""
        if not self.file_path:
            raise ValidationError("File has no file_path set.")
        if not os.path.exists(self.file_path):
            raise FileUploadError(f'File not found: "{self.file_path}"')
        if self.file_type != FileType.CSV:
            raise ValidationError(
                f"File type {self.file_type} is not supported for dataset conversion; expected CSV."
            )
        if not query_column or not isinstance(query_column, str):
            raise ValidationError("query_column must be a non-empty string.")

    def to_dataset(
        self,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        query_column: str = "query",
        reference_column: Optional[str] = "reference",
        metadata_columns: Optional[Sequence[str]] = None,
        **read_csv_kwargs,
    ) -> "Dataset":
        """Convert this CSV-backed File into a Dataset.

        Validates that the file is a CSV and that ``query_column`` is a valid
        parameter before delegating to :meth:`Dataset.from_csv`.

        Args:
            name: Dataset name. Defaults to this File's name, then the CSV filename.
            description: Optional dataset description.
            query_column: Required column holding each case's query. Defaults to "query".
            reference_column: Optional column holding each case's reference/expected value.
            metadata_columns: Optional extra columns to fold into each case's metadata.
            **read_csv_kwargs: Forwarded to ``pandas.read_csv``.
        """
        self._require_csv(query_column)
        from .agent_evaluator import Dataset

        return Dataset.from_csv(
            self.file_path,
            name=name or self.name,
            description=description,
            query_column=query_column,
            reference_column=reference_column,
            metadata_columns=metadata_columns,
            **read_csv_kwargs,
        )

    def preview_dataset(
        self,
        *,
        query_column: str = "query",
        reference_column: Optional[str] = "reference",
        metadata_columns: Optional[Sequence[str]] = None,
        **read_csv_kwargs,
    ) -> DatasetPreview:
        """Validate this CSV-backed File and report what's present for dataset conversion.

        Runs the same validation as :meth:`to_dataset` (file exists, is a CSV,
        contains ``query_column``) but does not build a Dataset - it only reports
        column names, row count, and which optional columns were found.

        Args:
            query_column: Required column holding each case's query. Defaults to "query".
            reference_column: Optional column holding each case's reference/expected value.
            metadata_columns: Optional extra columns to check for.
            **read_csv_kwargs: Forwarded to ``pandas.read_csv``.
        """
        self._require_csv(query_column)
        df = pd.read_csv(self.file_path, **read_csv_kwargs)
        if query_column not in df.columns:
            raise ValidationError(f"CSV must include query column {query_column!r}")

        requested_meta = list(metadata_columns) if metadata_columns else []
        found_meta = [c for c in requested_meta if c in df.columns]
        missing_meta = [c for c in requested_meta if c not in df.columns]
        ref_present = bool(reference_column) and reference_column in df.columns
        accounted_for = {query_column, *([reference_column] if ref_present else []), *found_meta}
        other_columns = [c for c in df.columns if c not in accounted_for]

        return DatasetPreview(
            num_rows=len(df),
            columns=list(df.columns),
            query_column=query_column,
            reference_column=reference_column if ref_present else None,
            metadata_columns_found=found_meta,
            metadata_columns_missing=missing_meta,
            other_columns=other_columns,
        )
