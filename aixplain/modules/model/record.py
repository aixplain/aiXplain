from aixplain.enums import DataType, StorageType
from typing import Optional
from uuid import uuid4


class Record:
    """A class representing a record in an index.

    This class defines the structure of a record with its value, type, ID, URI,
    and attributes.
    """
    def __init__(
        self,
        value: str = "",
        value_type: DataType = DataType.TEXT,
        id: Optional[str] = None,
        uri: str = "",
        attributes: dict = {},
    ):
        """Initialize a new Record instance.

        Args:
            value (str): The value of the record.
            value_type (DataType): The type of the value.
            id (Optional[str]): The ID of the record. Defaults to a random UUID.
            uri (str): The URI of the record.
            attributes (dict): The attributes of the record.
        """
        self.value = value
        self.value_type = value_type
        self.id = id if id is not None else str(uuid4())
        self.uri = uri
        self.attributes = attributes

    def to_dict(self):
        """Convert the record to a dictionary.

        Returns:
            dict: A dictionary containing the record's value, type, ID, URI, and attributes.
        """
        return {
            "data": self.value,
            "dataType": str(self.value_type),
            "document_id": self.id,
            "uri": self.uri,
            "attributes": self.attributes,
        }

    def validate(self):
        """Validate the record.

        Raises:
            AssertionError: If the value type is invalid or if the URI is required for image records.
        """
        from aixplain.factories import FileFactory
        from aixplain.modules.model.utils import is_supported_image_type

        assert self.value_type in [DataType.TEXT, DataType.IMAGE], "Index Upsert Error: Invalid value type"
        if self.value_type == DataType.IMAGE:
            assert self.uri is not None and self.uri != "", "Index Upsert Error: URI is required for image records"
        else:
            assert self.value is not None and self.value != "", "Index Upsert Error: Value is required for text records"

        storage_type = FileFactory.check_storage_type(self.uri)

        # Check if value is an image file or URL
        if storage_type in [StorageType.FILE, StorageType.URL]:
            if is_supported_image_type(self.uri):
                self.value_type = DataType.IMAGE
                self.uri = FileFactory.to_link(self.uri) if storage_type == StorageType.FILE else self.uri
            else:
                raise Exception(f"Index Upsert Error: Unsupported file type ({self.uri})")
