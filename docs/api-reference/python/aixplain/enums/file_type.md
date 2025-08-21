---
sidebar_label: file_type
title: aixplain.enums.file_type
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
Date: March 20th 2023
Description:
    File Type Enum

### FileType Objects

```python
class FileType(Enum)
```

[[view_source]](https://github.com/aixplain/aiXplain/blob/main/aixplain/enums/file_type.py#L27)

Enumeration of supported file types in the aiXplain system.

This enum defines the file extensions for various file formats that can be
processed by the system, including document, audio, image, and video formats.

**Attributes**:

- `CSV` _str_ - Comma-separated values file (.csv).
- `JSON` _str_ - JSON document file (.json).
- `TXT` _str_ - Plain text file (.txt).
- `XML` _str_ - XML document file (.xml).
- `FLAC` _str_ - Free Lossless Audio Codec file (.flac).
- `MP3` _str_ - MP3 audio file (.mp3).
- `WAV` _str_ - Waveform audio file (.wav).
- `JPEG` _str_ - JPEG image file (.jpeg).
- `PNG` _str_ - Portable Network Graphics file (.png).
- `JPG` _str_ - JPEG image file (.jpg).
- `JSON`0 _str_ - Graphics Interchange Format file (.gif).
- `JSON`1 _str_ - WebP image file (.webp).
- `JSON`2 _str_ - Audio Video Interleave file (.avi).
- `JSON`3 _str_ - MPEG-4 video file (.mp4).
- `JSON`4 _str_ - QuickTime movie file (.mov).
- `JSON`5 _str_ - MPEG-4 video file (.mpeg4).

