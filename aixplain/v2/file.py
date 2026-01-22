"""Simple Resource class for file handling and S3 uploads."""

import os
from typing import Optional, Union
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config

from .resource import (
    BaseResource,
    GetResourceMixin,
    SearchResourceMixin,
    BaseGetParams,
    BaseSearchParams,
)
from .upload_utils import FileUploader
from .enums import FileType


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
