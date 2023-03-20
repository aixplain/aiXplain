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
    License Enum
"""

from enum import Enum


class License(Enum):
    Apache_2 = "apache-2.0"
    BSD_2_CLAUSE = "bsd-2-clause"
    BSD_3_CLAUSE = "bsd-3-clause"
    BSD_3_CLAUSE_CLEAR = "bsd-3-clause-clear"
    CC_BY_4 = "cc-by-4.0"
    GNU_PUBLIC_2 = "gpl-2.0"
    GNU_PUBLIC_3 = "gpl-3.0"
    MIT = "mit"
