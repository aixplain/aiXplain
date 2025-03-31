from aixplain.factories.api_key_factory import APIKeyFactory
from aixplain.modules import APIKey, APIKeyLimits, APIKeyUsageLimit
from datetime import datetime, timedelta, timezone
import json
import pytest

from aixplain import aixplain_v2 as v2


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory, v2.APIKey])
def test_create_api_key_from_json(APIKeyFactory):
    api_key_json = "tests/functional/apikey/apikey.json"

    with open(api_key_json, "r") as file:
        api_key_data = json.load(file)

    expires_at = (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    unique_name = f"{api_key_data['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    api_key = APIKeyFactory.create(
        name=unique_name,
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
    assert api_key.name == unique_name

    api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory, v2.APIKey])
def test_create_api_key_from_dict(APIKeyFactory):
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
        "global_limits": {"token_per_minute": 100, "token_per_day": 1000, "request_per_day": 1000, "request_per_minute": 100},
        "budget": 1000,
        "expires_at": (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    unique_name = f"Test_API_Key_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    api_key = APIKeyFactory.create(
        name=unique_name,
        asset_limits=[APIKeyLimits(**limit) for limit in api_key_dict["asset_limits"]],
        global_limits=APIKeyLimits(**api_key_dict["global_limits"]),
        budget=api_key_dict["budget"],
        expires_at=datetime.strptime(api_key_dict["expires_at"], "%Y-%m-%dT%H:%M:%SZ"),
    )

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == unique_name

    api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory, v2.APIKey])
def test_create_update_api_key_from_dict(APIKeyFactory):
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
        "global_limits": {"token_per_minute": 100, "token_per_day": 1000, "request_per_day": 1000, "request_per_minute": 100},
        "budget": 1000,
        "expires_at": (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    unique_name = f"Test_API_Key_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    api_key = APIKeyFactory.create(
        name=unique_name,
        asset_limits=[APIKeyLimits(**limit) for limit in api_key_dict["asset_limits"]],
        global_limits=APIKeyLimits(**api_key_dict["global_limits"]),
        budget=api_key_dict["budget"],
        expires_at=datetime.strptime(api_key_dict["expires_at"], "%Y-%m-%dT%H:%M:%SZ"),
    )

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == unique_name

    api_key_ = APIKeyFactory.get(api_key=api_key.access_key)
    assert isinstance(api_key_, APIKey)
    assert api_key_.id != ""
    assert api_key_.name == unique_name

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

    api_key.delete()


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory, v2.APIKey])
def test_list_api_keys(APIKeyFactory):
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


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory, v2.APIKey])
def test_list_update_api_keys(APIKeyFactory):
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


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory, v2.APIKey])
def test_create_api_key_wrong_input(APIKeyFactory):
    api_key_name = "Test API Key"

    with pytest.raises(Exception):
        APIKeyFactory.create(
            name=api_key_name,
            asset_limits="invalid_limits",
            global_limits="invalid_limits",
            budget=-1000,
            expires_at="invalid_date",
        )
