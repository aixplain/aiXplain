from typing import List, TYPE_CHECKING
from typing_extensions import Unpack, NotRequired

from aixplain.v2.resource import BaseResource, CreateResourceMixin, BaseCreateParams

if TYPE_CHECKING:
    from aixplain.v2.enums import License, StorageType


class FileCreateParams(BaseCreateParams):
    """Parameters for creating a file."""

    local_path: str
    tags: NotRequired[List[str]]
    license: NotRequired["License"]
    is_temp: NotRequired[bool]


class File(BaseResource, CreateResourceMixin[FileCreateParams, "File"]):
    """Resource for files."""

    RESOURCE_PATH = "sdk/files"

    @classmethod
    def create(cls, *args, **kwargs: Unpack[FileCreateParams]) -> "File":
        """Create a file."""
        from aixplain.factories import FileFactory

        kwargs.setdefault("is_temp", True)
        kwargs.setdefault("license", None)
        kwargs.setdefault("tags", None)

        return FileFactory.create(*args, **kwargs)

    @classmethod
    def to_link(cls, local_path: str) -> str:
        """Convert a local path to a link.

        Args:
            local_path: str: The local path to the file.

        Returns:
            str: The link to the file.
        """
        from aixplain.factories import FileFactory

        return FileFactory.to_link(local_path)

    @classmethod
    def upload(
        cls,
        local_path: str,
        tags: List[str] = None,
        license: "License" = None,
        is_temp: bool = True,
    ) -> str:
        """Upload a file.

        Args:
            local_path: str: The local path to the file.

        Returns:
            str: The upload URL.
        """
        from aixplain.factories import FileFactory

        return FileFactory.upload(local_path, tags, license, is_temp)

    @classmethod
    def check_storage_type(cls, upload_url: str) -> "StorageType":
        """Check the storage type of a file.

        Args:
            upload_url: str: The upload URL.

        Returns:
            StorageType: The storage type of the file.
        """
        from aixplain.factories import FileFactory

        return FileFactory.check_storage_type(upload_url)
