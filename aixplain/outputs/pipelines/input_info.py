__author__ = "thiagocastroferreira"

"""
Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Thiago Castro Ferreira
Date: September 27th 2023
Description:
    Input Segment Info Class
"""

from aixplain.enums.data_type import DataType
from aixplain.enums.language import Language
from dataclasses import dataclass
from typing import Any, Optional, Union


@dataclass
class InputInfo:
    start: Union[float, int]
    end: Union[float, int]
    length: Union[float, int]
    is_url: bool
    data_type: DataType
    input_segment: Any
    language: Optional[Language] = None
