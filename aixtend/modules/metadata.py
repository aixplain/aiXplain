__author__ = "aiXplain"

from aixtend.enums.data_type import DataType
from aixtend.enums.file_type import FileType
from aixtend.enums.privacy import Privacy
from aixtend.enums.storage_type import StorageType
from typing import List, Optional


class MetaData:
    def __init__(
        self,
        name: str,
        dtype: DataType,
        storage_type: StorageType,
        privacy: Optional[Privacy] = None,
        file_extension: Optional[FileType] = None,
        **kwargs
    ) -> None:
        self.name = name
        if isinstance(dtype, str):
            dtype = DataType(dtype)
        self.dtype = dtype

        if isinstance(storage_type, str):
            storage_type = StorageType(storage_type)
        self.storage_type = storage_type

        if isinstance(privacy, str):
            privacy = Privacy(privacy)
        self.privacy = privacy
        self.file_extension = file_extension
        self.kwargs = kwargs
