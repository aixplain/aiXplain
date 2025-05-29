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
Date: February 17th 2025
Description:
    Embedding Model Enum
"""

from enum import Enum


class EmbeddingModel(str, Enum):
    OPENAI_ADA002 = "6734c55df127847059324d9e"
    JINA_CLIP_V2_MULTIMODAL = "67c5f705d8f6a65d6f74d732"
    MULTILINGUAL_E5_LARGE = "67efd0772a0a850afa045af3"
    BGE_M3 = "67efd4f92a0a850afa045af7"

    def __str__(self):
        return self._value_
