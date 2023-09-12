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


# Fixture to set up httpretty
"""@pytest.fixture
def setup_httpretty():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()"""

# Fixture to create a test AixplainClient
@pytest.fixture
def create_test_client():
    base_url = 'https://api.example.com'  # Set your base URL here
    client = AixplainClient(base_url, team_api_key='your_api_key')
    return client

# Test BaseAsset
def test_base_asset_attribute_access(setup_httpretty, create_test_client):
    asset = MockAsset({'id': '123', 'name': 'Mock Asset'})
    assert asset.id == '123'
    assert asset.name == 'Mock Asset'

def test_base_asset_missing_attribute(setup_httpretty, create_test_client):
    asset = MockAsset({'id': '123'})
    with pytest.raises(AttributeError):
        _ = asset.name

def test_base_asset_action_with_missing_id(setup_httpretty):
    asset = MockAsset({})  # Create a MockAsset without an 'id'
    with pytest.raises(AttributeError):
        _ = asset._action(method='GET')

def test_list_assets_with_custom_page_fn(setup_httpretty, create_test_client):
    base_url = create_test_client.base_url
    
    # Define a custom page function that always returns one asset
    def custom_page(page_number, filters=None, **kwargs):
        return [MockAsset({'id': '123'})]

    assets = ListAssetMixinWithAssetPath.list(n=2, page_fn=custom_page)  # Use the mixin with asset_path defined
    assert len(assets) == 2
    assert assets[0].id == '123'
    assert assets[1].id == '123'