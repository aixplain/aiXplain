import os
import pytest

@pytest.fixture(autouse=True)
def setup_env_variables():
    os.environ['BACKEND_URL'] = 'https://api.example.com'
    os.environ['MODELS_RUN_URL'] = 'https://api.example.com/api/v1/execute/'
    os.environ['TEAM_API_KEY'] = 'some_api_key'
    yield
    del os.environ['BACKEND_URL']
    del os.environ['MODELS_RUN_URL']
    del os.environ['TEAM_API_KEY']
