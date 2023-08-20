__author__ = "michaellam"

import json
import pytest
import requests_mock
from pathlib import Path
from aixplain.utils import config

from aixplain.factories.model_factory import ModelFactory
from aixplain.factories.dataset_factory import DatasetFactory
from aixplain.factories.metric_factory import MetricFactory

AUTH_FIXED_HEADER = {"Authorization": f"Token {config.TEAM_API_KEY}", "Content-Type": "application/json"}
API_FIXED_HEADER = {"x-api-key": f"{config.TEAM_API_KEY}", "Content-Type": "application/json"}


def test_login():
    url =  f"{config.BACKEND_URL}/sdk/ecr/login"
    with requests_mock.Mocker() as mock:
        with open(Path("tests/mock_responses/login_response.json")) as f:
            mock_json = json.load(f)
        mock.get(url, headers=AUTH_FIXED_HEADER, json=mock_json)
        creds = ModelFactory.asset_repo_login(config.TEAM_API_KEY)
    creds_dict = creds.to_dict()
    mock_dict = mock_json.to_dict()
    assert creds_dict == mock_dict