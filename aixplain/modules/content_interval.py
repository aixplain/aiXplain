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

Author: aiXplain team
Date: June 6th 2023
Description:
    Content Interval
"""

from dataclasses import dataclass
from typing import List, Optional, Text, Tuple, Union


@dataclass
class ContentInterval:
    content: Text
    content_id: int


@dataclass
class TextContentInterval(ContentInterval):
    start: Union[int, Tuple[int, int]]
    end: Union[int, Tuple[int, int]]


@dataclass
class AudioContentInterval(ContentInterval):
    start_time: float
    end_time: float


@dataclass
class ImageContentInterval(ContentInterval):
    x: Union[float, List[float]]
    y: Union[float, List[float]]
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None


@dataclass
class VideoContentInterval(ContentInterval):
    start_time: float
    end_time: float
    x: Optional[Union[float, List[float]]] = None
    y: Optional[Union[float, List[float]]] = None
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None
