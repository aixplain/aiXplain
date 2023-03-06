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
        data_column: Optional[str] = None,
        start_time_column: Optional[str] = None,
        end_time_column: Optional[str] = None,
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

        if data_column is None:
            self.data_column = name
        else:
            self.data_column = data_column

        self.start_time_column = start_time_column
        self.end_time_column = end_time_column

        if isinstance(privacy, str):
            privacy = Privacy(privacy)
        self.privacy = privacy
        self.file_extension = file_extension
        self.kwargs = kwargs
