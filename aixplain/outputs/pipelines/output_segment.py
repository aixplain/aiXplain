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
    Output Segment Class
"""

from aixplain.enums.data_type import DataType
from aixplain.enums.language import Language
from aixplain.outputs.pipelines.input_info import InputInfo
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Text


@dataclass
class OutputSegment:
    index: int
    status: Text
    response: Any
    is_url: bool
    data_type: DataType
    details: Dict = field(default_factory=dict)
    supplier_response: Optional[Any] = None
    language: Optional[Language] = None
    input_info: Optional[InputInfo] = None
