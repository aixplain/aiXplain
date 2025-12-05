__author__ = "aiXplain"

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
Date: March 20th 2023
Description:
    File Type Enum
"""

from enum import Enum


class FileType(Enum):
    """Enumeration of supported file types in the aiXplain system.

    This enum defines the file extensions for various file formats that can be
    processed by the system, including document, audio, image, and video formats.

    Attributes:
        CSV (str): Comma-separated values file (.csv).
        JSON (str): JSON document file (.json).
        TXT (str): Plain text file (.txt).
        XML (str): XML document file (.xml).
        FLAC (str): Free Lossless Audio Codec file (.flac).
        MP3 (str): MP3 audio file (.mp3).
        WAV (str): Waveform audio file (.wav).
        JPEG (str): JPEG image file (.jpeg).
        PNG (str): Portable Network Graphics file (.png).
        JPG (str): JPEG image file (.jpg).
        GIF (str): Graphics Interchange Format file (.gif).
        WEBP (str): WebP image file (.webp).
        AVI (str): Audio Video Interleave file (.avi).
        MP4 (str): MPEG-4 video file (.mp4).
        MOV (str): QuickTime movie file (.mov).
        MPEG4 (str): MPEG-4 video file (.mpeg4).
    """
    CSV = ".csv"
    JSON = ".json"
    TXT = ".txt"
    XML = ".xml"
    FLAC = ".flac"
    MP3 = ".mp3"
    WAV = ".wav"
    JPEG = ".jpeg"
    PNG = ".png"
    JPG = ".jpg"
    GIF = ".gif"
    WEBP = ".webp"
    AVI = ".avi"
    MP4 = ".mp4"
    MOV = ".mov"
    MPEG4 = ".mpeg4"
