import pytest
import httpretty
import os
from urllib.parse import urljoin
from aixplain.assets.files import File
from aixplain.enums import StorageType

COMMON_PATH = 'test/test_models.py'
BASE_URL = os.getenv('BACKEND_URL', 'https://api.example.com/')

"""@pytest.fixture
def setup_httpretty():
    httpretty.enable()
    yield
    httpretty.disable()
    httpretty.reset()
"""

def test_check_storage_type_file():
    storage_type = File.check_storage_type(COMMON_PATH)
    assert storage_type == StorageType.FILE

@httpretty.activate
def test_batch_upload_to_s3_dict():
    upload_url = urljoin(BASE_URL, "/upload").replace('.', '-')
    httpretty.register_uri(httpretty.POST, urljoin(BASE_URL,'sdk/file/upload/temp-url'),
                           json={'contentType': 'test/csv', 'originalName': COMMON_PATH}, status=200, body=f'{{"key": "the_key", "uploadUrl":"{upload_url}"}}')
    httpretty.register_uri(httpretty.PUT, upload_url, status=200)
    input_dict = {'file_path': COMMON_PATH}
    result = File.batch_upload_to_s3(input_dict)
    
    expected_result = {'file_path': 's3://api-example-com/the_key'}
    assert result == expected_result

@httpretty.activate
def test_batch_upload_to_s3_string():
    upload_url = urljoin(BASE_URL, "/upload").replace('.', '-')
    httpretty.register_uri(
        httpretty.POST,
        urljoin(BASE_URL,'sdk/file/upload/temp-url'),
        json={'contentType': 'test/csv', 'originalName': COMMON_PATH},
        status=200,
        body=f'{{"key": "the_key", "uploadUrl":"{upload_url}"}}')

    httpretty.register_uri(
        httpretty.PUT,
        upload_url,
        status=200)
    
    input_string = COMMON_PATH
    result = File.batch_upload_to_s3(input_string)
    
    expected_result = 's3://api-example-com/the_key'
    assert result == expected_result
