---
sidebar_label: content_interval
title: aixplain.modules.content_interval
---

#### \_\_author\_\_

Copyright 2023 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the &quot;License&quot;);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an &quot;AS IS&quot; BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: aiXplain team
Date: June 6th 2023
Description:
    Content Interval

### ContentInterval Objects

```python
@dataclass
class ContentInterval()
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/content_interval.py#L29)

Base class for representing intervals or segments within content.

This class serves as the base for more specific content interval types
like text, audio, image, and video intervals.

**Attributes**:

- `content` _Text_ - The actual content within the interval.
- `content_id` _int_ - ID of the content interval.

### TextContentInterval Objects

```python
@dataclass
class TextContentInterval(ContentInterval)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/content_interval.py#L44)

Class representing an interval or segment within text content.

This class extends ContentInterval to handle text-specific intervals,
supporting both character-based and line-column-based positions.

**Attributes**:

- `content` _Text_ - The text content within the interval.
- `content_id` _int_ - ID of the content interval.
- `start` _Union[int, Tuple[int, int]]_ - Starting position of the interval.
  Can be either a character offset (int) or a line-column tuple (int, int).
- `end` _Union[int, Tuple[int, int]]_ - Ending position of the interval.
  Can be either a character offset (int) or a line-column tuple (int, int).

### AudioContentInterval Objects

```python
@dataclass
class AudioContentInterval(ContentInterval)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/content_interval.py#L63)

Class representing an interval or segment within audio content.

This class extends ContentInterval to handle audio-specific intervals
using timestamps.

**Attributes**:

- `content` _Text_ - The audio content within the interval.
- `content_id` _int_ - ID of the content interval.
- `start_time` _float_ - Starting timestamp of the interval in seconds.
- `end_time` _float_ - Ending timestamp of the interval in seconds.

### ImageContentInterval Objects

```python
@dataclass
class ImageContentInterval(ContentInterval)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/content_interval.py#L80)

Class representing an interval or region within image content.

This class extends ContentInterval to handle image-specific regions,
supporting both single points and polygons through coordinates.

**Attributes**:

- `content` _Text_ - The image content within the interval.
- `content_id` _int_ - ID of the content interval.
- `x` _Union[float, List[float]]_ - X-coordinate(s) of the region.
  Single float for rectangular regions, list for polygon vertices.
- `y` _Union[float, List[float]]_ - Y-coordinate(s) of the region.
  Single float for rectangular regions, list for polygon vertices.
- `width` _Optional[float]_ - Width of the region in pixels. Only used for
  rectangular regions. Defaults to None.
- `height` _Optional[float]_ - Height of the region in pixels. Only used for
  rectangular regions. Defaults to None.
- `rotation` _Optional[float]_ - Rotation angle of the region in degrees.
  Defaults to None.

### VideoContentInterval Objects

```python
@dataclass
class VideoContentInterval(ContentInterval)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/modules/content_interval.py#L108)

Class representing an interval or region within video content.

This class extends ContentInterval to handle video-specific intervals,
combining temporal information with optional spatial regions.

**Attributes**:

- `content` _Text_ - The video content within the interval.
- `content_id` _int_ - ID of the content interval.
- `start_time` _float_ - Starting timestamp of the interval in seconds.
- `end_time` _float_ - Ending timestamp of the interval in seconds.
- `x` _Optional[Union[float, List[float]]], optional_ - X-coordinate(s) of the region.
  Single float for rectangular regions, list for polygon vertices.
  Defaults to None.
- `y` _Optional[Union[float, List[float]]], optional_ - Y-coordinate(s) of the region.
  Single float for rectangular regions, list for polygon vertices.
  Defaults to None.
- `width` _Optional[float], optional_ - Width of the region in pixels.
  Only used for rectangular regions. Defaults to None.
- `height` _Optional[float], optional_ - Height of the region in pixels.
  Only used for rectangular regions. Defaults to None.
- `rotation` _Optional[float], optional_ - Rotation angle of the region in degrees.
  Defaults to None.

