import pytest
import os

from unittest.mock import Mock
from requests import Response

from aixplain.client import AixplainClient
from aixplain.config import TEAM_API_KEY

class MockSession(Mock):
    def request(self, method, url, **kwargs):
        response = Response()
        response.status_code = 200
        return response

@pytest.mark.parametrize("api_key", [TEAM_API_KEY])
def test_successful_get_request(api_key):
    client = AixplainClient(base_url='http://mock-test.com', aixplain_api_key=api_key)
    client.session = MockSession()
    response = client.get('/path')
    assert response.status_code == 200

def test_invalid_api_keys():
    with pytest.raises(ValueError):
        AixplainClient(base_url='http://mock-test.com')

@pytest.mark.parametrize("api_key", [TEAM_API_KEY])
def test_condition_aixplain_api_key(api_key):
    client = AixplainClient(base_url='http://mock-test.com', aixplain_api_key=api_key)
    assert 'x-aixplain-key' in client.session.headers

@pytest.mark.parametrize("api_key", [TEAM_API_KEY])
def test_condition_team_api_key(api_key):
    client = AixplainClient(base_url='http://mock-test.com', team_api_key=api_key)
    assert 'x-api-key' in client.session.headers

@pytest.mark.parametrize("api_key", [TEAM_API_KEY])
def test_post_request(api_key):
    client = AixplainClient(base_url='http://mock-test.com', aixplain_api_key=api_key)
    client.session = MockSession()
    response = client.request('POST', '/path', json={'data': 'value'})
    assert response.status_code == 200

@pytest.mark.parametrize("api_key", [TEAM_API_KEY])
def test_session_reuse(api_key):
    # test using the same session more than one time 
    client = AixplainClient(base_url='http://mock-test.com', aixplain_api_key=api_key)
    session_id_before = id(client.session)
    client.get('/path')
    session_id_after = id(client.session)
    assert session_id_before == session_id_after