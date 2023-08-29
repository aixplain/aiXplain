import pytest
import httpretty
from aixplain.client import AixplainClient
from aixplain.assets.files import File
from aixplain.enums import StorageType

COMMON_PATH = 'test/test_models.py'

@pytest.fixture
def setup_httpretty():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()

@pytest.fixture
def create_test_client():
    base_url = 'https://api.example.com'
    client = AixplainClient(base_url, team_api_key='your_api_key')
    return client

def test_check_storage_type_file():
    storage_type = File.check_storage_type(COMMON_PATH)
    assert storage_type == StorageType.FILE
@pytest.mark.skip()
def test_batch_upload_to_s3_dict(setup_httpretty, create_test_client):
    httpretty.register_uri(httpretty.POST, 'https://api.example.com/file/upload/temp-url',
                           json={'key': 's3-key', 'uploadUrl': 'https://s3-upload-url.com'}, status=200)
    import pdb
    pdb.set_trace()
    input_dict = {'file_path': COMMON_PATH}
    result = File.batch_upload_to_s3(input_dict)
    
    expected_result = {'file_path': 's3://s3-upload-url.com/s3-key'}
    assert result == expected_result
@pytest.mark.skip()
def test_batch_upload_to_s3_string(setup_httpretty, create_test_client):
    httpretty.register_uri(httpretty.POST, 'https://api.example.com/file/upload/temp-url',
                           json={'key': 's3-key', 'uploadUrl': 'https://s3-upload-url.com'}, status=200)
    
    input_string = COMMON_PATH
    result = File.batch_upload_to_s3(input_string)
    
    expected_result = 's3://s3-upload-url.com/s3-key'
    assert result == expected_result
