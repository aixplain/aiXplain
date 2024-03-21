__author__ = "thiagocastroferreira"

"""
Copyright 2024 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Author: Duraikrishna Selvaraju, Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: February 21st 2024
Description:
    Asset Enum
"""

from enum import Enum
from typing import Text

class AssetStatus(Text, Enum):
    HIDDEN = 'hidden'
    SCHEDULED = 'scheduled'
    ONBOARDING = 'onboarding'
    ONBOARDED = 'onboarded'
    PENDING = 'pending'
    FAILED = 'failed'
    TRAINING = 'training'
    REJECTED = 'rejected'
    ENABLING = 'enabling'
    DELETING = 'deleting'
    DISABLED = 'disabled'
    DELETED = 'deleted'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELING = 'canceling'
    CANCELED = 'canceled'