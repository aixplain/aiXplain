from aixplain.factories.api_key_factory import APIKeyFactory
from aixplain.modules import APIKey, APIKeyLimits, APIKeyUsageLimit
from aixplain.modules.api_key import TokenType
from datetime import datetime, timedelta, timezone
import json
import pytest
import time

# Single test API key name - reused across all tests
TEST_API_KEY_NAME = "TEST_API_KEY_FUNCTIONAL"


def _get_test_api_key(APIKeyFactory):
    """Get the test API key if it exists."""
    try:
        api_keys = APIKeyFactory.list()
        for api_key in api_keys:
            if api_key.name == TEST_API_KEY_NAME:
                return api_key
    except Exception:
        pass
    return None


def _delete_test_api_key(APIKeyFactory):
    """Delete the test API key if it exists."""
    api_key = _get_test_api_key(APIKeyFactory)
    if api_key:
        try:
            api_key.delete()
            time.sleep(0.5)  # Wait for deletion to process
        except Exception:
            pass


@pytest.fixture(scope="module", autouse=True)
def test_api_key_lifecycle():
    """Setup/Teardown: Manage single test API key lifecycle.

    Setup: Delete test key before all tests start
    Teardown: Delete test key after all tests complete
    """
    # Setup: Delete test key before tests start
    _delete_test_api_key(APIKeyFactory)
    yield
    # Teardown: Delete test key after all tests complete
    _delete_test_api_key(APIKeyFactory)


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_01_create_api_key_from_json(APIKeyFactory):
    """Test creating API key from JSON file."""
    api_key_json = "tests/functional/apikey/apikey.json"

    with open(api_key_json, "r") as file:
        api_key_data = json.load(file)

    expires_at = (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")

    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[
            APIKeyLimits(
                model=api_key_data["asset_limits"][0]["model"],
                token_per_minute=api_key_data["asset_limits"][0]["token_per_minute"],
                token_per_day=api_key_data["asset_limits"][0]["token_per_day"],
                request_per_day=api_key_data["asset_limits"][0]["request_per_day"],
                request_per_minute=api_key_data["asset_limits"][0]["request_per_minute"],
            )
        ],
        global_limits=APIKeyLimits(
            token_per_minute=api_key_data["global_limits"]["token_per_minute"],
            token_per_day=api_key_data["global_limits"]["token_per_day"],
            request_per_day=api_key_data["global_limits"]["request_per_day"],
            request_per_minute=api_key_data["global_limits"]["request_per_minute"],
        ),
        budget=api_key_data["budget"],
        expires_at=expires_at,
    )

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == TEST_API_KEY_NAME

    # Cleanup: Delete the key after test
    api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_02_create_api_key_from_dict(APIKeyFactory):
    """Test creating API key from dictionary."""
    api_key_dict = {
        "asset_limits": [
            {
                "model": "640b517694bf816d35a59125",
                "token_per_minute": 100,
                "token_per_day": 1000,
                "request_per_day": 1000,
                "request_per_minute": 100,
            }
        ],
        "global_limits": {
            "token_per_minute": 100,
            "token_per_day": 1000,
            "request_per_day": 1000,
            "request_per_minute": 100,
        },
        "budget": 1000,
        "expires_at": (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[APIKeyLimits(**limit) for limit in api_key_dict["asset_limits"]],
        global_limits=APIKeyLimits(**api_key_dict["global_limits"]),
        budget=api_key_dict["budget"],
        expires_at=datetime.strptime(api_key_dict["expires_at"], "%Y-%m-%dT%H:%M:%SZ"),
    )

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == TEST_API_KEY_NAME

    # Cleanup: Delete the key after test
    api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_03_create_update_api_key_from_dict(APIKeyFactory):
    """Test creating and updating API key from dictionary."""
    api_key_dict = {
        "asset_limits": [
            {
                "model": "640b517694bf816d35a59125",
                "token_per_minute": 100,
                "token_per_day": 1000,
                "request_per_day": 1000,
                "request_per_minute": 100,
            }
        ],
        "global_limits": {
            "token_per_minute": 100,
            "token_per_day": 1000,
            "request_per_day": 1000,
            "request_per_minute": 100,
        },
        "budget": 1000,
        "expires_at": (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[APIKeyLimits(**limit) for limit in api_key_dict["asset_limits"]],
        global_limits=APIKeyLimits(**api_key_dict["global_limits"]),
        budget=api_key_dict["budget"],
        expires_at=datetime.strptime(api_key_dict["expires_at"], "%Y-%m-%dT%H:%M:%SZ"),
    )

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == TEST_API_KEY_NAME

    api_key_ = APIKeyFactory.get(api_key=api_key.access_key)
    assert isinstance(api_key_, APIKey)
    assert api_key_.id != ""
    assert api_key_.name == TEST_API_KEY_NAME

    api_key.global_limits.token_per_day = 222
    api_key.global_limits.token_per_minute = 222
    api_key.global_limits.request_per_day = 222
    api_key.global_limits.request_per_minute = 222
    api_key.asset_limits[0].request_per_day = 222
    api_key.asset_limits[0].request_per_minute = 222
    api_key.asset_limits[0].token_per_day = 222
    api_key.asset_limits[0].token_per_minute = 222
    api_key = APIKeyFactory.update(api_key)

    assert api_key.global_limits.token_per_day == 222
    assert api_key.global_limits.token_per_minute == 222
    assert api_key.global_limits.request_per_day == 222
    assert api_key.global_limits.request_per_minute == 222
    assert api_key.asset_limits[0].request_per_day == 222
    assert api_key.asset_limits[0].request_per_minute == 222
    assert api_key.asset_limits[0].token_per_day == 222
    assert api_key.asset_limits[0].token_per_minute == 222

    # Cleanup: Delete the key after test
    api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_04_list_api_keys(APIKeyFactory):
    """Test listing API keys."""
    api_keys = APIKeyFactory.list()
    assert isinstance(api_keys, list)

    for api_key in api_keys:
        assert isinstance(api_key, APIKey)
        assert api_key.id != ""

        if api_key.is_admin is False:
            usage = api_key.get_usage()
            assert isinstance(usage, list)
            if len(usage) > 0:
                assert isinstance(usage[0], APIKeyUsageLimit)


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_05_list_update_api_keys(APIKeyFactory):
    """Test listing and updating API keys."""
    api_keys = APIKeyFactory.list()
    assert isinstance(api_keys, list)

    for api_key in api_keys:
        assert isinstance(api_key, APIKey)
        assert api_key.id != ""

        from random import randint

        number = randint(0, 10000)
        if api_key.global_limits is None:
            api_key.global_limits = APIKeyLimits(
                token_per_minute=number,
                token_per_day=number,
                request_per_day=number,
                request_per_minute=number,
            )
        else:
            api_key.global_limits.token_per_day = number
            api_key.global_limits.token_per_minute = number
            api_key.global_limits.request_per_day = number
            api_key.global_limits.request_per_minute = number

        if api_key.asset_limits is None:
            api_key.asset_limits = []

        if len(api_key.asset_limits) == 0:
            api_key.asset_limits.append(
                APIKeyLimits(
                    model="640b517694bf816d35a59125",
                    token_per_minute=number,
                    token_per_day=number,
                    request_per_day=number,
                    request_per_minute=number,
                )
            )
        else:
            api_key.asset_limits[0].request_per_day = number
            api_key.asset_limits[0].request_per_minute = number
            api_key.asset_limits[0].token_per_day = number
            api_key.asset_limits[0].token_per_minute = number
        api_key = APIKeyFactory.update(api_key)

        assert api_key.global_limits.token_per_day == number
        assert api_key.global_limits.token_per_minute == number
        assert api_key.global_limits.request_per_day == number
        assert api_key.global_limits.request_per_minute == number
        assert api_key.asset_limits[0].request_per_day == number
        assert api_key.asset_limits[0].request_per_minute == number
        assert api_key.asset_limits[0].token_per_day == number
        assert api_key.asset_limits[0].token_per_minute == number
        break


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_06_create_api_key_wrong_input(APIKeyFactory):
    """Test API key creation with invalid input (should raise exception)."""
    api_key_name = "Test API Key"

    with pytest.raises(Exception):
        APIKeyFactory.create(
            name=api_key_name,
            asset_limits="invalid_limits",
            global_limits="invalid_limits",
            budget=-1000,
            expires_at="invalid_date",
        )


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_07_create_api_key_with_token_type_input(APIKeyFactory):
    """Test creating API key with token_type set to INPUT."""
    expires_at = (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    api_key = None

    try:
        api_key = APIKeyFactory.create(
            name=TEST_API_KEY_NAME,
            asset_limits=[
                APIKeyLimits(
                    model="640b517694bf816d35a59125",
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
                token_type=TokenType.INPUT,
            ),
            budget=1000,
            expires_at=expires_at,
        )

        assert isinstance(api_key, APIKey)
        assert api_key.id != ""
        assert api_key.name == TEST_API_KEY_NAME
        assert api_key.global_limits.token_type == TokenType.INPUT
        assert api_key.asset_limits[0].token_type == TokenType.INPUT
    finally:
        if api_key:
            api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_08_create_api_key_with_token_type_output(APIKeyFactory):
    """Test creating API key with token_type set to OUTPUT."""
    expires_at = (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    api_key = None

    try:
        api_key = APIKeyFactory.create(
            name=TEST_API_KEY_NAME,
            asset_limits=[
                APIKeyLimits(
                    model="640b517694bf816d35a59125",
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
                token_type=TokenType.OUTPUT,
            ),
            budget=1000,
            expires_at=expires_at,
        )

        assert isinstance(api_key, APIKey)
        assert api_key.id != ""
        assert api_key.global_limits.token_type == TokenType.OUTPUT
        assert api_key.asset_limits[0].token_type == TokenType.OUTPUT
    finally:
        if api_key:
            api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_09_create_api_key_with_token_type_total(APIKeyFactory):
    """Test creating API key with token_type set to TOTAL."""
    expires_at = (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    api_key = None

    try:
        api_key = APIKeyFactory.create(
            name=TEST_API_KEY_NAME,
            asset_limits=[
                APIKeyLimits(
                    model="640b517694bf816d35a59125",
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_day=1000,
                    request_per_minute=100,
                    token_type=TokenType.TOTAL,
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
            expires_at=expires_at,
        )

        assert isinstance(api_key, APIKey)
        assert api_key.id != ""
        assert api_key.global_limits.token_type == TokenType.TOTAL
        assert api_key.asset_limits[0].token_type == TokenType.TOTAL
    finally:
        if api_key:
            api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_10_update_api_key_token_type(APIKeyFactory):
    """Test updating API key token_type."""
    expires_at = (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    api_key = None

    try:
        # Create with INPUT token_type
        api_key = APIKeyFactory.create(
            name=TEST_API_KEY_NAME,
            asset_limits=[
                APIKeyLimits(
                    model="640b517694bf816d35a59125",
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
                token_type=TokenType.INPUT,
            ),
            budget=1000,
            expires_at=expires_at,
        )

        assert api_key.global_limits.token_type == TokenType.INPUT

        # Update to OUTPUT token_type
        api_key.global_limits.token_type = TokenType.OUTPUT
        api_key.asset_limits[0].token_type = TokenType.OUTPUT
        updated_api_key = APIKeyFactory.update(api_key)

        assert updated_api_key.global_limits.token_type == TokenType.OUTPUT
        assert updated_api_key.asset_limits[0].token_type == TokenType.OUTPUT
    finally:
        if api_key:
            api_key.delete()
