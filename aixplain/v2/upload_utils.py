"""File upload utilities for v2 Resource system.

This module provides comprehensive file upload functionality that ports the exact
logic from the legacy FileFactory while maintaining a clean, modular architecture.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin
import requests

from .exceptions import FileUploadError


class FileValidator:
    """Handles file validation logic."""

    # File size limits (in bytes) - ported from legacy
    SIZE_LIMITS = {
        "audio": 52428800,  # 50MB
        "application": 26214400,  # 25MB
        "video": 314572800,  # 300MB
        "image": 26214400,  # 25MB
        "other": 52428800,  # 50MB
        "database": 314572800,  # 300MB
    }

    @classmethod
    def validate_file_exists(cls, file_path: str) -> None:
        """Validate that the file exists."""
        if not os.path.exists(file_path):
            raise FileUploadError(f'File Upload Error: local file "{file_path}" not found.')

    @classmethod
    def validate_file_size(cls, file_path: str, file_type: str) -> None:
        """Validate file size against type-specific limits."""
        file_size = os.path.getsize(file_path)
        max_size = cls.SIZE_LIMITS.get(file_type, cls.SIZE_LIMITS["other"])

        if file_size > max_size:
            raise FileUploadError(
                f'File Upload Error: local file "{file_path}" of type "{file_type}" exceeds {max_size / 1048576} MB.'
            )

    @classmethod
    def get_file_size_mb(cls, file_path: str) -> float:
        """Get file size in MB."""
        return os.path.getsize(file_path) / 1048576


class MimeTypeDetector:
    """Handles MIME type detection with fallback support."""

    # Extension to MIME type mapping for fallback
    EXTENSION_MAPPING = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".txt": "text/plain",
        ".pdf": "application/pdf",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".flac": "audio/flac",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".db": "application/x-sqlite3",
        ".sqlite": "application/x-sqlite3",
        ".sqlite3": "application/x-sqlite3",
    }

    @classmethod
    def detect_mime_type(cls, file_path: str) -> str:
        """Detect MIME type with fallback support."""
        # Try filetype library first
        try:
            import filetype

            mime_type = filetype.guess_mime(file_path)
            if mime_type:
                return mime_type
        except ImportError:
            pass

        # Fallback to extension-based detection
        ext = Path(file_path).suffix.lower()
        return cls.EXTENSION_MAPPING.get(ext, "text/csv")

    @classmethod
    def classify_file_type(cls, file_path: str, mime_type: str) -> str:
        """Classify file type for size limit enforcement."""
        # Special case for database files
        if file_path.endswith((".db", ".sqlite", ".sqlite3")):
            return "database"

        # Extract main type from MIME type
        if mime_type and "/" in mime_type:
            main_type = mime_type.split("/")[0]
            if main_type in FileValidator.SIZE_LIMITS:
                return main_type

        # Default to "other"
        return "other"


class RequestManager:
    """Handles HTTP requests with retry logic."""

    @classmethod
    def create_session(cls) -> requests.Session:
        """Create a requests session with retry configuration."""
        from .client import create_retry_session

        return create_retry_session()

    @classmethod
    def request_with_retry(cls, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic."""
        session = cls.create_session()
        return session.request(method=method.upper(), url=url, **kwargs)


class PresignedUrlManager:
    """Handles pre-signed URL requests to aiXplain backend."""

    @classmethod
    def get_temp_upload_url(cls, backend_url: str) -> str:
        """Get temporary upload URL endpoint."""
        return urljoin(backend_url, "sdk/file/upload/temp-url")

    @classmethod
    def get_perm_upload_url(cls, backend_url: str) -> str:
        """Get permanent upload URL endpoint."""
        return urljoin(backend_url, "sdk/file/upload-url")

    @classmethod
    def build_temp_payload(cls, content_type: str, file_name: str) -> Dict[str, str]:
        """Build payload for temporary upload request."""
        return {
            "contentType": content_type,
            "originalName": file_name,
        }

    @classmethod
    def build_perm_payload(cls, content_type: str, file_path: str, tags: List[str], license: str) -> Dict[str, str]:
        """Build payload for permanent upload request."""
        return {
            "contentType": content_type,
            "originalName": file_path,
            "tags": ",".join(tags),
            "license": license,
        }

    @classmethod
    def request_presigned_url(cls, url: str, payload: Dict[str, str], api_key: str) -> Dict[str, Any]:
        """Request pre-signed URL from backend."""
        headers = {"Authorization": f"token {api_key}"}

        try:
            response = RequestManager.request_with_retry("post", url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FileUploadError(f"File Upload Error: Failed to get pre-signed URL: {e}")


class S3Uploader:
    """Handles S3 file uploads using pre-signed URLs."""

    @classmethod
    def upload_file(cls, file_path: str, presigned_url: str, content_type: str) -> None:
        """Upload file to S3 using pre-signed URL."""
        headers = {"Content-Type": content_type}

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            response = RequestManager.request_with_retry("put", presigned_url, headers=headers, data=file_data)

            if response.status_code != 200:
                raise FileUploadError("File Uploading Error: Failure on Uploading to S3.")

        except Exception as e:
            raise FileUploadError(f"File Uploading Error: {e}")

    @classmethod
    def construct_s3_url(cls, presigned_url: str, path: str) -> str:
        """Construct S3 URL from pre-signed URL and path."""
        # Extract bucket name from presigned URL
        bucket_match = re.findall(r"https://(.*?).s3.amazonaws.com", presigned_url)
        if bucket_match:
            bucket_name = bucket_match[0]
            return f"s3://{bucket_name}/{path}"
        else:
            # Fallback: use the path directly
            return f"s3://aixplain-uploads/{path}"


class ConfigManager:
    """Handles configuration and environment variables."""

    @classmethod
    def get_backend_url(cls, custom_url: Optional[str] = None) -> str:
        """Get backend URL from custom value or environment."""
        return custom_url or os.getenv("BACKEND_URL", "https://platform-api.aixplain.com")

    @classmethod
    def get_api_key(cls, custom_key: Optional[str] = None, required: bool = True) -> str:
        """Get API key from custom value or environment."""
        api_key = custom_key or os.getenv("TEAM_API_KEY", "")
        if not api_key and required:
            raise FileUploadError("File Upload Error: API key is required for file uploads.")
        return api_key


class FileUploader:
    """Main file upload orchestrator."""

    def __init__(
        self,
        backend_url: Optional[str] = None,
        api_key: Optional[str] = None,
        require_api_key: bool = True,
    ):
        """Initialize file uploader with configuration."""
        self.backend_url = ConfigManager.get_backend_url(backend_url)
        self.api_key = ConfigManager.get_api_key(api_key, required=require_api_key)

    def upload(
        self,
        file_path: str,
        tags: Optional[List[str]] = None,
        license: str = "MIT",
        is_temp: bool = True,
        return_download_link: bool = False,
    ) -> str:
        """Upload a file to S3 using the same logic as legacy FileFactory.

        Args:
            file_path: Path to the file to upload
            tags: Tags to associate with the file
            license: License type for the file
            is_temp: Whether this is a temporary upload
            return_download_link: Whether to return download link instead of S3 path

        Returns:
            S3 path (s3://bucket/key) or download URL

        Raises:
            FileUploadError: If upload fails
        """
        # Step 1: Validate file
        FileValidator.validate_file_exists(file_path)

        # Step 2: Detect MIME type and classify file
        mime_type = MimeTypeDetector.detect_mime_type(file_path)
        file_type = MimeTypeDetector.classify_file_type(file_path, mime_type)
        content_type = mime_type or "text/csv"

        # Step 3: Validate file size
        FileValidator.validate_file_size(file_path, file_type)

        # Step 4: Get pre-signed URL
        if is_temp:
            url = PresignedUrlManager.get_temp_upload_url(self.backend_url)
            payload = PresignedUrlManager.build_temp_payload(content_type, os.path.basename(file_path))
        else:
            url = PresignedUrlManager.get_perm_upload_url(self.backend_url)
            if tags is None:
                tags = []
            payload = PresignedUrlManager.build_perm_payload(content_type, file_path, tags, license)

        response_data = PresignedUrlManager.request_presigned_url(url, payload, self.api_key)

        # Step 5: Upload file to S3
        path = response_data["key"]
        presigned_url = response_data["uploadUrl"]
        download_link = response_data.get("downloadUrl", "")

        S3Uploader.upload_file(file_path, presigned_url, content_type)

        # Step 6: Return appropriate URL
        if return_download_link:
            return download_link
        else:
            return S3Uploader.construct_s3_url(presigned_url, path)


# Convenience functions for easy usage
def upload_file(
    file_path: str,
    tags: Optional[List[str]] = None,
    license: str = "MIT",
    is_temp: bool = True,
    return_download_link: bool = False,
    backend_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Convenience function to upload a file.

    Args:
        file_path: Path to the file to upload
        tags: Tags to associate with the file
        license: License type for the file
        is_temp: Whether this is a temporary upload
        return_download_link: Whether to return download link instead of S3 path
        backend_url: Custom backend URL (optional)
        api_key: Custom API key (optional)

    Returns:
        S3 path (s3://bucket/key) or download URL
    """
    uploader = FileUploader(backend_url=backend_url, api_key=api_key)
    return uploader.upload(
        file_path=file_path,
        tags=tags,
        license=license,
        is_temp=is_temp,
        return_download_link=return_download_link,
    )


def validate_file_for_upload(file_path: str) -> Dict[str, Any]:
    """Validate a file for upload without actually uploading.

    Args:
        file_path: Path to the file to validate

    Returns:
        Dictionary with validation results

    Raises:
        FileUploadError: If validation fails
    """
    # Validate file exists
    FileValidator.validate_file_exists(file_path)

    # Detect MIME type and classify
    mime_type = MimeTypeDetector.detect_mime_type(file_path)
    file_type = MimeTypeDetector.classify_file_type(file_path, mime_type)

    # Validate file size
    FileValidator.validate_file_size(file_path, file_type)

    # Get file info
    file_size_mb = FileValidator.get_file_size_mb(file_path)
    max_size_mb = FileValidator.SIZE_LIMITS[file_type] / 1048576

    return {
        "file_path": file_path,
        "mime_type": mime_type,
        "file_type": file_type,
        "file_size_mb": round(file_size_mb, 3),
        "max_size_mb": max_size_mb,
        "valid": True,
    }
