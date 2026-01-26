__author__ = "aixplain"
from aixplain.modules import APIKeyLimits
from aixplain.modules.api_key import TokenType
from datetime import datetime
import requests_mock
import aixplain.utils.config as config
from aixplain.factories.api_key_factory import APIKeyFactory
import json


def read_data(data_path):
    return json.load(open(data_path, "r"))


def test_api_key_service():
    with requests_mock.Mocker() as mock:
        model_id = "test_asset_id"
        model_url = f"{config.BACKEND_URL}/sdk/models/{model_id}"
        model_map = read_data("tests/unit/mock_responses/model_response.json")
        mock.get(model_url, json=model_map)

        create_url = f"{config.BACKEND_URL}/sdk/api-keys"
        api_key_response = {
            "id": "key-id",
            "name": "Name",
            "accessKey": "access-key",
            "budget": 1000,
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100},
            "assetsLimits": [{"assetId": model_id, "tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100}],
            "expiresAt": "2024-10-07T00:00:00Z",
            "isAdmin": False,
        }
        mock.post(create_url, json=api_key_response)

        api_key = APIKeyFactory.create(
            name="Test API Key",
            asset_limits=[
                APIKeyLimits(
                    model=model_id,
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_day=1000,
                    request_per_minute=100,
                )
            ],
            global_limits=APIKeyLimits(
                token_per_minute=100, token_per_day=1000, request_per_day=1000, request_per_minute=100
            ),
            budget=1000,
            expires_at=datetime(2024, 10, 7),
        )

        assert api_key.id == api_key_response["id"]
        assert api_key.access_key == api_key_response["accessKey"]
        assert api_key.budget == api_key_response["budget"]
        assert api_key.expires_at == api_key_response["expiresAt"]

        # List test
        list_url = f"{config.BACKEND_URL}/sdk/api-keys"
        mock.get(list_url, json=[api_key_response])

        api_keys = APIKeyFactory.list()

        assert len(api_keys) == 1
        assert api_keys[0].id == api_key_response["id"]
        assert api_keys[0].access_key == api_key_response["accessKey"]

        # Delete Test:
        delete_url = f"{config.BACKEND_URL}/sdk/api-keys/{api_key.id}"
        mock.delete(delete_url, status_code=200)

        api_key.delete()


def test_setters():
    with requests_mock.Mocker() as mock:
        model_id = "test_asset_id"
        model_url = f"{config.BACKEND_URL}/sdk/models/{model_id}"
        model_map = read_data("tests/unit/mock_responses/model_response.json")
        mock.get(model_url, json=model_map)

        create_url = f"{config.BACKEND_URL}/sdk/api-keys"
        api_key_response = {
            "id": "key-id",
            "name": "Name",
            "accessKey": "access-key",
            "budget": 1000,
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100},
            "assetsLimits": [{"assetId": model_id, "tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100}],
            "expiresAt": "2024-10-07T00:00:00Z",
            "isAdmin": False,
        }
        mock.post(create_url, json=api_key_response)

        api_key = APIKeyFactory.create(
            name="Test API Key",
            asset_limits=[
                APIKeyLimits(
                    model=model_id,
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_day=1000,
                    request_per_minute=100,
                )
            ],
            global_limits=APIKeyLimits(
                token_per_minute=100, token_per_day=1000, request_per_day=1000, request_per_minute=100
            ),
            budget=1000,
            expires_at=datetime(2024, 10, 7),
        )

    api_key.set_token_per_day(1)
    api_key.set_token_per_minute(1)
    api_key.set_request_per_day(1)
    api_key.set_request_per_minute(1)
    api_key.set_token_per_day(1, model_id)
    api_key.set_token_per_minute(1, model_id)
    api_key.set_request_per_day(1, model_id)
    api_key.set_request_per_minute(1, model_id)

    assert api_key.asset_limits[0].token_per_day == 1
    assert api_key.asset_limits[0].token_per_minute == 1
    assert api_key.asset_limits[0].request_per_day == 1
    assert api_key.asset_limits[0].request_per_minute == 1
    assert api_key.global_limits.token_per_day == 1
    assert api_key.global_limits.token_per_minute == 1
    assert api_key.global_limits.request_per_day == 1
    assert api_key.global_limits.request_per_minute == 1


def test_token_type_enum():
    """Test TokenType enum values."""
    assert TokenType.INPUT.value == "input"
    assert TokenType.OUTPUT.value == "output"
    assert TokenType.TOTAL.value == "total"


def test_api_key_limits_with_token_type():
    """Test creating APIKeyLimits with token_type parameter."""
    limits = APIKeyLimits(
        token_per_minute=100,
        token_per_day=1000,
        request_per_minute=10,
        request_per_day=100,
        token_type=TokenType.INPUT,
    )
    assert limits.token_type == TokenType.INPUT

    limits_output = APIKeyLimits(
        token_per_minute=100,
        token_per_day=1000,
        request_per_minute=10,
        request_per_day=100,
        token_type=TokenType.OUTPUT,
    )
    assert limits_output.token_type == TokenType.OUTPUT

    limits_none = APIKeyLimits(
        token_per_minute=100,
        token_per_day=1000,
        request_per_minute=10,
        request_per_day=100,
    )
    assert limits_none.token_type is None


def test_api_key_with_token_type_from_response():
    """Test parsing tokenType from API response."""
    with requests_mock.Mocker() as mock:
        model_id = "test_asset_id"
        model_url = f"{config.BACKEND_URL}/sdk/models/{model_id}"
        model_map = read_data("tests/unit/mock_responses/model_response.json")
        mock.get(model_url, json=model_map)

        create_url = f"{config.BACKEND_URL}/sdk/api-keys"
        api_key_response = {
            "id": "key-id",
            "name": "Name",
            "accessKey": "access-key",
            "budget": 1000,
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100, "tokenType": "input"},
            "assetsLimits": [
                {"assetId": model_id, "tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100, "tokenType": "output"}
            ],
            "expiresAt": "2024-10-07T00:00:00Z",
            "isAdmin": False,
        }
        mock.post(create_url, json=api_key_response)

        api_key = APIKeyFactory.create(
            name="Test API Key",
            asset_limits=[
                APIKeyLimits(
                    model=model_id,
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_day=1000,
                    request_per_minute=100,
                    token_type=TokenType.OUTPUT,
                )
            ],
            global_limits=APIKeyLimits(
                token_per_minute=100,
                token_per_day=1000,
                request_per_day=1000,
                request_per_minute=100,
                token_type=TokenType.INPUT,
            ),
            budget=1000,
            expires_at=datetime(2024, 10, 7),
        )

        assert api_key.global_limits.token_type == TokenType.INPUT
        assert api_key.asset_limits[0].token_type == TokenType.OUTPUT


def test_api_key_without_token_type_in_response():
    """Test parsing API response without tokenType (should default to None)."""
    with requests_mock.Mocker() as mock:
        model_id = "test_asset_id"
        model_url = f"{config.BACKEND_URL}/sdk/models/{model_id}"
        model_map = read_data("tests/unit/mock_responses/model_response.json")
        mock.get(model_url, json=model_map)

        create_url = f"{config.BACKEND_URL}/sdk/api-keys"
        api_key_response = {
            "id": "key-id",
            "name": "Name",
            "accessKey": "access-key",
            "budget": 1000,
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100},
            "assetsLimits": [{"assetId": model_id, "tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100}],
            "expiresAt": "2024-10-07T00:00:00Z",
            "isAdmin": False,
        }
        mock.post(create_url, json=api_key_response)

        api_key = APIKeyFactory.create(
            name="Test API Key",
            asset_limits=[
                APIKeyLimits(
                    model=model_id,
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_day=1000,
                    request_per_minute=100,
                )
            ],
            global_limits=APIKeyLimits(
                token_per_minute=100, token_per_day=1000, request_per_day=1000, request_per_minute=100
            ),
            budget=1000,
            expires_at=datetime(2024, 10, 7),
        )

        assert api_key.global_limits.token_type is None
        assert api_key.asset_limits[0].token_type is None


def test_api_key_to_dict_with_token_type():
    """Test to_dict() serialization with token_type."""
    with requests_mock.Mocker() as mock:
        model_id = "test_asset_id"
        model_url = f"{config.BACKEND_URL}/sdk/models/{model_id}"
        model_map = read_data("tests/unit/mock_responses/model_response.json")
        mock.get(model_url, json=model_map)

        create_url = f"{config.BACKEND_URL}/sdk/api-keys"
        api_key_response = {
            "id": "key-id",
            "name": "Name",
            "accessKey": "access-key",
            "budget": 1000,
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100, "tokenType": "total"},
            "assetsLimits": [
                {"assetId": model_id, "tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100, "tokenType": "input"}
            ],
            "expiresAt": "2024-10-07T00:00:00Z",
            "isAdmin": False,
        }
        mock.post(create_url, json=api_key_response)

        api_key = APIKeyFactory.create(
            name="Test API Key",
            asset_limits=[
                APIKeyLimits(
                    model=model_id,
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_day=1000,
                    request_per_minute=100,
                    token_type=TokenType.INPUT,
                )
            ],
            global_limits=APIKeyLimits(
                token_per_minute=100,
                token_per_day=1000,
                request_per_day=1000,
                request_per_minute=100,
                token_type=TokenType.TOTAL,
            ),
            budget=1000,
            expires_at=datetime(2024, 10, 7),
        )

        payload = api_key.to_dict()

        assert payload["globalLimits"]["tokenType"] == "total"
        assert payload["assetsLimits"][0]["tokenType"] == "input"


def test_api_key_to_dict_without_token_type():
    """Test to_dict() serialization without token_type (should be None)."""
    with requests_mock.Mocker() as mock:
        model_id = "test_asset_id"
        model_url = f"{config.BACKEND_URL}/sdk/models/{model_id}"
        model_map = read_data("tests/unit/mock_responses/model_response.json")
        mock.get(model_url, json=model_map)

        create_url = f"{config.BACKEND_URL}/sdk/api-keys"
        api_key_response = {
            "id": "key-id",
            "name": "Name",
            "accessKey": "access-key",
            "budget": 1000,
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100},
            "assetsLimits": [{"assetId": model_id, "tpm": 100, "tpd": 1000, "rpd": 1000, "rpm": 100}],
            "expiresAt": "2024-10-07T00:00:00Z",
            "isAdmin": False,
        }
        mock.post(create_url, json=api_key_response)

        api_key = APIKeyFactory.create(
            name="Test API Key",
            asset_limits=[
                APIKeyLimits(
                    model=model_id,
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_day=1000,
                    request_per_minute=100,
                )
            ],
            global_limits=APIKeyLimits(
                token_per_minute=100, token_per_day=1000, request_per_day=1000, request_per_minute=100
            ),
            budget=1000,
            expires_at=datetime(2024, 10, 7),
        )

        payload = api_key.to_dict()

        assert payload["globalLimits"]["tokenType"] is None
        assert payload["assetsLimits"][0]["tokenType"] is None


if __name__ == "__main__":
    test_setters()
