import pytest
import httpretty
from aixplain.client import AixplainClient
from aixplain.assets.base import BaseAsset, GetAssetMixin, ListAssetMixin

# Define a mock subclass of BaseAsset for testing
class MockAsset(BaseAsset):
    asset_path = 'mock_assets'

    def __init__(self, obj):
        super().__init__(obj)

# Define the asset_path attribute in GetAssetMixin
class GetAssetMixinWithAssetPath(BaseAsset, GetAssetMixin):
    asset_path = 'mock_assets'  # Define your asset path here
    def __init__(self, obj):
        super().__init__(obj)

# Define the asset_path attribute in ListAssetMixin
class ListAssetMixinWithAssetPath(BaseAsset, ListAssetMixin):
    asset_path = 'mock_assets'  # Define your asset path here
    def __init__(self, obj):
        super().__init__(obj)

# Test BaseAsset
def test_base_asset_attribute_access():
    asset = MockAsset({'id': '123', 'name': 'Mock Asset'})
    assert asset.id == '123'
    assert asset.name == 'Mock Asset'

def test_base_asset_missing_attribute():
    asset = MockAsset({'id': '123'})
    with pytest.raises(AttributeError):
        _ = asset.name

def test_base_asset_action_with_missing_id():
    asset = MockAsset({})  # Create a MockAsset without an 'id'
    with pytest.raises(AttributeError):
        _ = asset._action(method='GET')

def test_list_assets_with_custom_page_fn():
    
    # Define a custom page function that always returns one asset
    def custom_page(page_number, filters=None, **kwargs):
        return [MockAsset({'id': '123'})]

    assets = ListAssetMixinWithAssetPath.list(n=2, page_fn=custom_page)  # Use the mixin with asset_path defined
    assert len(assets) == 2
    assert assets[0].id == '123'
    assert assets[1].id == '123'