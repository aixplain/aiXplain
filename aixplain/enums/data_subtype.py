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
Date: May 3rd 2023
Description:
    Data Subtype Enum
"""

from enum import Enum


class DataSubtype(Enum):
    AGE = "age"
    GENDER = "gender"
    INTERVAL = "interval"
    OTHER = "other"
    RACE = "race"
    SPLIT = "split"
    TOPIC = "topic"
    
    def __str__(self):
        return self._value_
