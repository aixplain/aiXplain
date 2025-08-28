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
    """Base class for representing intervals or segments within content.

    This class serves as the base for more specific content interval types
    like text, audio, image, and video intervals.

    Attributes:
        content (Text): The actual content within the interval.
        content_id (int): ID of the content interval.
    """
    content: Text
    content_id: int


@dataclass
class TextContentInterval(ContentInterval):
    """Class representing an interval or segment within text content.

    This class extends ContentInterval to handle text-specific intervals,
    supporting both character-based and line-column-based positions.

    Attributes:
        content (Text): The text content within the interval.
        content_id (int): ID of the content interval.
        start (Union[int, Tuple[int, int]]): Starting position of the interval.
            Can be either a character offset (int) or a line-column tuple (int, int).
        end (Union[int, Tuple[int, int]]): Ending position of the interval.
            Can be either a character offset (int) or a line-column tuple (int, int).
    """
    start: Union[int, Tuple[int, int]]
    end: Union[int, Tuple[int, int]]


@dataclass
class AudioContentInterval(ContentInterval):
    """Class representing an interval or segment within audio content.

    This class extends ContentInterval to handle audio-specific intervals
    using timestamps.

    Attributes:
        content (Text): The audio content within the interval.
        content_id (int): ID of the content interval.
        start_time (float): Starting timestamp of the interval in seconds.
        end_time (float): Ending timestamp of the interval in seconds.
    """
    start_time: float
    end_time: float


@dataclass
class ImageContentInterval(ContentInterval):
    """Class representing an interval or region within image content.

    This class extends ContentInterval to handle image-specific regions,
    supporting both single points and polygons through coordinates.

    Attributes:
        content (Text): The image content within the interval.
        content_id (int): ID of the content interval.
        x (Union[float, List[float]]): X-coordinate(s) of the region.
            Single float for rectangular regions, list for polygon vertices.
        y (Union[float, List[float]]): Y-coordinate(s) of the region.
            Single float for rectangular regions, list for polygon vertices.
        width (Optional[float]): Width of the region in pixels. Only used for
            rectangular regions. Defaults to None.
        height (Optional[float]): Height of the region in pixels. Only used for
            rectangular regions. Defaults to None.
        rotation (Optional[float]): Rotation angle of the region in degrees.
            Defaults to None.
    """
    x: Union[float, List[float]]
    y: Union[float, List[float]]
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None


@dataclass
class VideoContentInterval(ContentInterval):
    """Class representing an interval or region within video content.

    This class extends ContentInterval to handle video-specific intervals,
    combining temporal information with optional spatial regions.

    Attributes:
        content (Text): The video content within the interval.
        content_id (int): ID of the content interval.
        start_time (float): Starting timestamp of the interval in seconds.
        end_time (float): Ending timestamp of the interval in seconds.
        x (Optional[Union[float, List[float]]], optional): X-coordinate(s) of the region.
            Single float for rectangular regions, list for polygon vertices.
            Defaults to None.
        y (Optional[Union[float, List[float]]], optional): Y-coordinate(s) of the region.
            Single float for rectangular regions, list for polygon vertices.
            Defaults to None.
        width (Optional[float], optional): Width of the region in pixels.
            Only used for rectangular regions. Defaults to None.
        height (Optional[float], optional): Height of the region in pixels.
            Only used for rectangular regions. Defaults to None.
        rotation (Optional[float], optional): Rotation angle of the region in degrees.
            Defaults to None.
    """
    start_time: float
    end_time: float
    x: Optional[Union[float, List[float]]] = None
    y: Optional[Union[float, List[float]]] = None
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None
