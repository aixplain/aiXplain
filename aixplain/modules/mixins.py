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

Author: Thiago Castro Ferreira, Shreyas Sharma and Lucas Pavanelli
Date: November 25th 2024
Description:
    Mixins for common functionality across different asset types
"""
from abc import ABC
from typing import List, TypeVar, Generic, Optional
from aixplain.enums import AssetStatus

T = TypeVar("T")


class DeployableMixin(ABC, Generic[T]):
    """A mixin that provides common deployment-related functionality for assets.

    This mixin provides methods for:
    1. Filtering items that are not onboarded
    2. Validating if an asset is ready to be deployed
    3. Deploying an asset

    Classes that inherit from this mixin should:
    1. Implement _validate_deployment_readiness to call the parent implementation with their specific asset type
    2. Optionally override deploy() if they need special deployment handling
    """

    def _filter_not_onboarded_items(self, items: List[T]) -> List[T]:
        """Filter a list of items to return only those not in ONBOARDED status.

        Args:
            items (List[T]): List of items to filter

        Returns:
            List[T]: List of items not in ONBOARDED status
        """
        return [item for item in items if item.status != AssetStatus.ONBOARDED]

    def _validate_deployment_readiness(self, items: Optional[List[T]] = None) -> None:
        """Validate if the asset is ready to be deployed.

        Args:
            asset_type (str): Type of asset being validated (e.g. "Agent", "Team Agent", "Pipeline")
            items (Optional[List[T]], optional): List of items to validate (e.g. tools for Agent, agents for TeamAgent)

        Raises:
            ValueError: If the asset is not ready to be deployed
        """
        asset_type = self.__class__.__name__
        if self.status == AssetStatus.ONBOARDED:
            raise ValueError(f"{asset_type} is already deployed.")

        if self.status != AssetStatus.DRAFT:
            raise ValueError(f"{asset_type} must be in DRAFT status to be deployed.")

        if items:
            not_onboarded = self._filter_not_onboarded_items(items)
            if not_onboarded:
                items_str = ", ".join(item.name for item in not_onboarded)
                raise ValueError(f"All {asset_type.lower()} items must be deployed first. " f"Not deployed items: {items_str}")

    def deploy(self) -> None:
        """Deploy the asset.

        This method validates that the asset is ready to be deployed and updates its status to ONBOARDED.
        Classes that need special deployment handling should override this method.

        Raises:
            ValueError: If the asset is not ready to be deployed
        """
        self._validate_deployment_readiness()
        self.status = AssetStatus.ONBOARDED
        self.update()
