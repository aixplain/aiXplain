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
    """Enumeration of possible status values for an asset in the aiXplain system.

    This enum defines all possible states that an asset can be in throughout its lifecycle,
    from creation to deletion. Each enum value corresponds to a specific state in the
    asset's lifecycle.

    Attributes:
        DRAFT (str): Initial state for a newly created asset.
        HIDDEN (str): Asset is hidden from public view.
        SCHEDULED (str): Asset is scheduled for processing.
        ONBOARDING (str): Asset is in the process of being onboarded.
        ONBOARDED (str): Asset has been successfully onboarded.
        PENDING (str): Asset is waiting for processing.
        FAILED (str): Asset processing has failed.
        TRAINING (str): Asset is currently in training.
        REJECTED (str): Asset has been rejected.
        ENABLING (str): Asset is in the process of being enabled.
        DELETING (str): Asset is in the process of being deleted.
        DISABLED (str): Asset has been disabled.
        DELETED (str): Asset has been deleted.
        IN_PROGRESS (str): Asset is currently being processed.
        COMPLETED (str): Asset has completed processing.
        CANCELING (str): Asset operation is being canceled.
        CANCELED (str): Asset operation has been canceled.
        DEPRECATED_DRAFT (str): Draft state that has been deprecated.
    """
    DRAFT = "draft"
    HIDDEN = "hidden"
    SCHEDULED = "scheduled"
    ONBOARDING = "onboarding"
    ONBOARDED = "onboarded"
    PENDING = "pending"
    FAILED = "failed"
    TRAINING = "training"
    REJECTED = "rejected"
    ENABLING = "enabling"
    DELETING = "deleting"
    DISABLED = "disabled"
    DELETED = "deleted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELING = "canceling"
    CANCELED = "canceled"
    DEPRECATED_DRAFT = "deprecated_draft"
