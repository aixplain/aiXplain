from aixplain.modules.asset import Asset
from typing import Optional, List


class AssetRouter:
    _assets: Optional[List[Asset]] = None

    def __init__(self, assets: Optional[List[Asset]] = None):
        self._assets = assets

    @property
    def assets(self):
        return self._assets

    @assets.setter
    def assets(self, assets: List[Asset]):
        self._assets = assets
