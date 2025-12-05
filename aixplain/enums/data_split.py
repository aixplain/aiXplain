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
    Data Split Enum
"""

from enum import Enum


class DataSplit(Enum):
    """Enumeration of dataset split types.

    This enum defines the standard dataset split types used for machine learning tasks,
    including training, validation, and testing splits.

    Attributes:
        TRAIN (str): Training dataset split used for model training.
        VALIDATION (str): Validation dataset split used for model tuning.
        TEST (str): Test dataset split used for final model evaluation.
    """
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"
