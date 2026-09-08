"""Functional tests for API key management (BUG-947).

Two rules hold everywhere in this module, because breaking either of them
mutated the production tenant on every push to `main`:

1. **Only ever touch a key this test created.** `test_05` used to take the first
   key ``APIKeyFactory.list()`` returned -- whatever real key that happened to
   be -- rewrite its global and asset limits to ``randint(0, 10000)``, and never
   restore them.
2. **Delete by identity, never by name.** A module-scoped autouse fixture used
   to enumerate every key in the tenant and delete any matching a generic name
   from a hardcoded list -- a name a real team member could plausibly have used
   -- with the failure swallowed. :data:`TEST_API_KEY_NAME` therefore carries a
   per-session uuid, so a name match is provably ours, and even then the delete
   goes through the object handle rather than a name filter.

Cleanup is the shared `resource_tracker` fixture (tests/functional/conftest.py):
append the key right after creating it and teardown deletes it whether the body
passes, fails, or errors -- including once per `flaky` rerun.
"""

import logging
from datetime import datetime, timedelta, timezone
from random import randint
from uuid import uuid4

import json
import pytest

from aixplain.factories.api_key_factory import APIKeyFactory
from aixplain.modules import APIKey, APIKeyLimits, APIKeyUsageLimit
from aixplain.modules.api_key import TokenType

from tests.cleanup_guards import (
    LEAK_LEDGER,
    CleanupError,
    CleanupFailure,
    ResourceTracker,
    confirm_leaked,
    describe,
    strict_cleanup,
)

logger = logging.getLogger(__name__)

#: The model every test attaches its asset limits to.
TEST_MODEL_ID = "69b7e5f1b2fe44704ab0e7d0"

#: Unique per session, which is what makes the leak check below safe: a key with
#: this name can only have been created by this run, so two concurrent runs
#: cannot delete each other's keys mid-test and no human-chosen name can ever
#: match. The generic name the old sweep matched on is deliberately absent from
#: this whole directory, including `apikey.json`, which is where the literal came
#: from -- `tests/unit/test_functional_hygiene.py` fails if it returns.
TEST_API_KEY_NAME = f"TEST_API_KEY_FUNCTIONAL_{uuid4().hex[:8]}"


@pytest.fixture(scope="module", autouse=True)
def api_key_leak_check():
    """Detect keys this run created but did not register with `resource_tracker`.

    A net under the net. Detection matches on :data:`TEST_API_KEY_NAME`, so a
    match is provably ours; the deletion itself goes through the object handle.

    There is deliberately no *pre*-test sweep. Its only purpose was mopping up
    leftovers from previous runs, which is exactly what made it dangerous. With
    the tracker in place a leftover is a bug this check reports, and pre-existing
    orphans belong to the one-off tenant audit (BUG-947 suggestion 6).

    The listing runs immediately after the last test's teardown deleted its key
    and is not immediately consistent, so it is re-listed through
    :func:`confirm_leaked` before anything is called a leak. Deciding on the
    first listing would fail a clean run, and `APIKey.delete` reports every
    failure -- 404 included -- as one generic string, so the second delete could
    not tell us otherwise either.
    """
    yield
    try:
        leaked = confirm_leaked(
            lambda: [api_key for api_key in APIKeyFactory.list() if api_key.name == TEST_API_KEY_NAME]
        )
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        logger.error("BUG-947 leak check could not list API keys: %s", exc)
        return
    if not leaked:
        return

    failures = ResourceTracker(leaked).cleanup("apikey leak check")
    LEAK_LEDGER.extend(
        failures
        or [
            CleanupFailure("apikey leak check", describe(api_key), "leaked; deleted by the leak check")
            for api_key in leaked
        ]
    )
    if strict_cleanup():
        raise CleanupError(
            f"BUG-947: {len(leaked)} API key(s) named {TEST_API_KEY_NAME} outlived their test; "
            "a test created a key without registering it with resource_tracker."
        )


def _limits(**overrides) -> APIKeyLimits:
    """Build the standard test limits, with *overrides* applied."""
    values = {"token_per_minute": 100, "token_per_day": 1000, "request_per_day": 1000, "request_per_minute": 100}
    values.update(overrides)
    return APIKeyLimits(**values)


def _expires_in_four_weeks() -> str:
    return (datetime.now(timezone.utc) + timedelta(weeks=4)).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.mark.flaky(reruns=2, reruns_delay=5)
@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_01_create_api_key_from_json(resource_tracker, APIKeyFactory):
    """Test creating API key from JSON file."""
    api_key_json = "tests/functional/apikey/apikey.json"

    with open(api_key_json, "r") as file:
        api_key_data = json.load(file)

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
        expires_at=_expires_in_four_weeks(),
    )
    # Registered before the first assertion: each `flaky` rerun creates another
    # key, and the fixture teardown runs for every one of them.
    resource_tracker.append(api_key)

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == TEST_API_KEY_NAME


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_02_create_api_key_from_dict(resource_tracker, APIKeyFactory):
    """Test creating API key from dictionary."""
    api_key_dict = {
        "asset_limits": [
            {
                "model": TEST_MODEL_ID,
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
        "expires_at": _expires_in_four_weeks(),
    }

    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[APIKeyLimits(**limit) for limit in api_key_dict["asset_limits"]],
        global_limits=APIKeyLimits(**api_key_dict["global_limits"]),
        budget=api_key_dict["budget"],
        expires_at=datetime.strptime(api_key_dict["expires_at"], "%Y-%m-%dT%H:%M:%SZ"),
    )
    resource_tracker.append(api_key)

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == TEST_API_KEY_NAME


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_03_create_update_api_key_from_dict(resource_tracker, APIKeyFactory):
    """Test creating and updating API key from dictionary."""
    api_key_dict = {
        "asset_limits": [
            {
                "model": TEST_MODEL_ID,
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
        "expires_at": _expires_in_four_weeks(),
    }

    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[APIKeyLimits(**limit) for limit in api_key_dict["asset_limits"]],
        global_limits=APIKeyLimits(**api_key_dict["global_limits"]),
        budget=api_key_dict["budget"],
        expires_at=datetime.strptime(api_key_dict["expires_at"], "%Y-%m-%dT%H:%M:%SZ"),
    )
    resource_tracker.append(api_key)

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
    # `update` returns a fresh handle to the *same* key, so the original
    # registration already covers it; registering both would make teardown
    # delete twice and the second failure is indistinguishable from an outage.
    updated_api_key = APIKeyFactory.update(api_key)

    assert updated_api_key.global_limits.token_per_day == 222
    assert updated_api_key.global_limits.token_per_minute == 222
    assert updated_api_key.global_limits.request_per_day == 222
    assert updated_api_key.global_limits.request_per_minute == 222
    assert updated_api_key.asset_limits[0].request_per_day == 222
    assert updated_api_key.asset_limits[0].request_per_minute == 222
    assert updated_api_key.asset_limits[0].token_per_day == 222
    assert updated_api_key.asset_limits[0].token_per_minute == 222


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_04_list_api_keys(APIKeyFactory):
    """Test listing API keys.

    Read-only: it inspects every key in the tenant, so it must never write to
    one. Usage is a GET (BUG-947).
    """
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
def test_05_list_update_api_keys(resource_tracker, APIKeyFactory):
    """Test that a key this test created lists, and that its limits update.

    The previous version iterated ``APIKeyFactory.list()``, took the *first* key
    -- whatever real key that happened to be -- rewrote its global and asset
    limits to a random integer, asserted, and broke out of the loop without
    restoring anything. On `main` that silently randomised the rate limits of a
    live production key on every push, with no audit trail (BUG-947).

    The ``global_limits is None`` / empty ``asset_limits`` branches it used to
    carry are gone with it: they only existed to cope with an arbitrary foreign
    key, and a key this test just created always has both.
    """
    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[_limits(model=TEST_MODEL_ID)],
        global_limits=_limits(),
        budget=1000,
        expires_at=_expires_in_four_weeks(),
    )
    resource_tracker.append(api_key)

    # The listing half of the old test's coverage, kept strictly read-only.
    assert api_key.id in {listed.id for listed in APIKeyFactory.list()}

    number = randint(0, 10000)
    for limits in (api_key.global_limits, api_key.asset_limits[0]):
        limits.token_per_day = number
        limits.token_per_minute = number
        limits.request_per_day = number
        limits.request_per_minute = number
    # `update` returns a fresh handle to the *same* key, so the original
    # registration already covers it; registering both would make teardown
    # delete twice and the second failure is indistinguishable from an outage.
    updated_api_key = APIKeyFactory.update(api_key)

    assert updated_api_key.global_limits.token_per_day == number
    assert updated_api_key.global_limits.token_per_minute == number
    assert updated_api_key.global_limits.request_per_day == number
    assert updated_api_key.global_limits.request_per_minute == number
    assert updated_api_key.asset_limits[0].request_per_day == number
    assert updated_api_key.asset_limits[0].request_per_minute == number
    assert updated_api_key.asset_limits[0].token_per_day == number
    assert updated_api_key.asset_limits[0].token_per_minute == number


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_06_create_api_key_wrong_input(APIKeyFactory):
    """Test API key creation with invalid input (should raise exception).

    Uses :data:`TEST_API_KEY_NAME` rather than a generic literal so that if the
    backend ever *accepted* this payload, the resulting key would be attributable
    to this run and caught by :func:`api_key_leak_check` (BUG-947).
    """
    with pytest.raises(Exception):
        APIKeyFactory.create(
            name=TEST_API_KEY_NAME,
            asset_limits="invalid_limits",
            global_limits="invalid_limits",
            budget=-1000,
            expires_at="invalid_date",
        )


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_07_create_api_key_with_token_type_input(resource_tracker, APIKeyFactory):
    """Test creating API key with token_type set to INPUT."""
    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[_limits(model=TEST_MODEL_ID, token_type=TokenType.INPUT)],
        global_limits=_limits(token_type=TokenType.INPUT),
        budget=1000,
        expires_at=_expires_in_four_weeks(),
    )
    resource_tracker.append(api_key)

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.name == TEST_API_KEY_NAME
    assert api_key.global_limits.token_type == TokenType.INPUT
    assert api_key.asset_limits[0].token_type == TokenType.INPUT


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_08_create_api_key_with_token_type_output(resource_tracker, APIKeyFactory):
    """Test creating API key with token_type set to OUTPUT."""
    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[_limits(model=TEST_MODEL_ID, token_type=TokenType.OUTPUT)],
        global_limits=_limits(token_type=TokenType.OUTPUT),
        budget=1000,
        expires_at=_expires_in_four_weeks(),
    )
    resource_tracker.append(api_key)

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.global_limits.token_type == TokenType.OUTPUT
    assert api_key.asset_limits[0].token_type == TokenType.OUTPUT


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_09_create_api_key_with_token_type_total(resource_tracker, APIKeyFactory):
    """Test creating API key with token_type set to TOTAL."""
    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[_limits(model=TEST_MODEL_ID, token_type=TokenType.TOTAL)],
        global_limits=_limits(token_type=TokenType.TOTAL),
        budget=1000,
        expires_at=_expires_in_four_weeks(),
    )
    resource_tracker.append(api_key)

    assert isinstance(api_key, APIKey)
    assert api_key.id != ""
    assert api_key.global_limits.token_type == TokenType.TOTAL
    assert api_key.asset_limits[0].token_type == TokenType.TOTAL


@pytest.mark.parametrize("APIKeyFactory", [APIKeyFactory])
def test_10_update_api_key_token_type(resource_tracker, APIKeyFactory):
    """Test updating API key token_type."""
    # Create with INPUT token_type
    api_key = APIKeyFactory.create(
        name=TEST_API_KEY_NAME,
        asset_limits=[_limits(model=TEST_MODEL_ID, token_type=TokenType.INPUT)],
        global_limits=_limits(token_type=TokenType.INPUT),
        budget=1000,
        expires_at=_expires_in_four_weeks(),
    )
    resource_tracker.append(api_key)

    assert api_key.global_limits.token_type == TokenType.INPUT

    # Update to OUTPUT token_type
    api_key.global_limits.token_type = TokenType.OUTPUT
    api_key.asset_limits[0].token_type = TokenType.OUTPUT
    # `update` returns a fresh handle to the *same* key, so the original
    # registration already covers it; registering both would make teardown
    # delete twice and the second failure is indistinguishable from an outage.
    updated_api_key = APIKeyFactory.update(api_key)

    assert updated_api_key.global_limits.token_type == TokenType.OUTPUT
    assert updated_api_key.asset_limits[0].token_type == TokenType.OUTPUT
