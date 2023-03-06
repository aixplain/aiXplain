__author__ = "aiXplain"

from aixtend.modules.file import File
from aixtend.enums.data_type import DataType
from aixtend.enums.privacy import Privacy
from typing import Callable, List, Optional, Union


class Data:
    def __init__(
        self,
        id: str,
        name: str,
        dtype: DataType,
        privacy: Privacy,
        data_column: Optional[str] = None,
        files: Optional[List[File]] = [],
        transform_func: Optional[Union[str, Callable]] = None,
        **kwargs
    ) -> None:
        self.id = id
        self.name = name
        self.dtype = dtype
        self.privacy = privacy
        self.files = files
        if data_column is None:
            self.data_column = name
        else:
            self.data_column = data_column
        self.transform_func = transform_func
        self.kwargs = kwargs

    def transform(self, file: File) -> List:
        return self.transform_func(file)
