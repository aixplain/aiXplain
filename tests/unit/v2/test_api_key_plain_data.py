"""Tests for PROD-2917: API key limits as plain data, and a `get()` that resolves.

Four things had to change together, because they are the same few lines:

* limits take a dict on the user-facing field names, and reject a key that is
  neither a field nor a wire alias (a misspelled key used to be silently
  dropped, i.e. no limit at all);
* an unset dimension is distinguishable from a deliberate zero, so setting one
  dimension no longer writes zeros over the other three;
* ``get()`` resolves an ID, a key value or a name, instead of failing with "not
  found" when handed the thing v1's ``get()`` took;
* a key value is matched in full, not by its first and last four characters.
"""

import pytest
from unittest.mock import Mock

from aixplain.v2.api_key import (
    APIKey,
    APIKeyLimits,
    TokenType,
    coerce_limits,
    coerce_limits_list,
)
from aixplain.v2.exceptions import APIError, ResourceError, ValidationError


def _bound(listing, get_response=None, get_error=None):
    """Return an APIKey subclass bound to a stub client.

    Args:
        listing: What ``GET sdk/api-keys`` answers, i.e. what ``list()`` sees.
        get_response: What ``GET sdk/api-keys/<id>`` answers, if anything.
        get_error: Raised by the by-ID fetch instead, for the fallback paths.

    The default by-ID failure is an ``APIError`` carrying HTTP 404, which is what
    ``AixplainClient`` raises for an unknown id. It used to be a bare
    ``ResourceError``, which the client never raises here -- and ``get()`` now
    reads the status to decide whether falling back is meaningful, so a stub
    raising something the real client cannot would have tested nothing.
    """

    def get(path, **kwargs):
        if path == APIKey.RESOURCE_PATH:
            return listing
        if get_error is not None:
            raise get_error
        if get_response is None:
            raise APIError(f"Not found: {path}", status_code=404)
        return get_response

    client = Mock()
    client.get = Mock(side_effect=get)
    client.request = Mock(return_value=listing)

    class BoundAPIKey(APIKey):
        context = Mock(client=client)

    return BoundAPIKey


# -- Limits accept plain data -------------------------------------------------------


class TestLimitsFromDicts:
    """``asset_limits`` / ``global_limits`` accept dicts on the user-facing names."""

    def test_asset_limits_assignment_from_dicts(self):
        """The headline case: assign a list of dicts, read back objects."""
        key = APIKey(name="Test Key", budget=10.0)
        key.asset_limits = [{"model": "openai/gpt-5", "token_per_minute": 10000, "token_type": "output"}]

        assert isinstance(key.asset_limits[0], APIKeyLimits)
        assert key.asset_limits[0].token_per_minute == 10000
        assert key.asset_limits[0].model == "openai/gpt-5"
        assert key.asset_limits[0].token_type is TokenType.OUTPUT

    def test_asset_limits_dicts_reach_the_save_payload(self):
        """A dict assignment has to survive all the way to the wire."""
        key = APIKey(id="key1", name="Test Key", budget=10.0)
        key.asset_limits = [{"model": "model1", "token_per_minute": 10000, "token_type": "output"}]

        payload = key.build_save_payload()

        assert payload["assetsLimits"] == [{"tpm": 10000, "tokenType": "output", "assetId": "model1"}]

    def test_global_limits_assignment_from_dict(self):
        key = APIKey(name="Test Key", budget=10.0)
        key.global_limits = {"request_per_day": 500}

        assert isinstance(key.global_limits, APIKeyLimits)
        assert key.global_limits.request_per_day == 500

    def test_constructor_accepts_dicts_too(self):
        """Construction and assignment must not disagree about what they take."""
        key = APIKey(
            name="Test Key",
            global_limits={"token_per_day": 1000},
            asset_limits=[{"model": "m1", "token_per_minute": 5}],
        )

        assert key.global_limits.token_per_day == 1000
        assert key.asset_limits[0].token_per_minute == 5

    def test_mixed_dicts_and_objects(self):
        key = APIKey(name="Test Key")
        key.asset_limits = [{"model": "m1", "token_per_minute": 5}, APIKeyLimits(model="m2", token_per_day=9)]

        assert [limit.model for limit in key.asset_limits] == ["m1", "m2"]

    def test_wire_spellings_still_work(self):
        """``{"tpm": ...}`` worked before the user-facing names landed."""
        assert coerce_limits({"tpm": 100, "tpd": 1000}).token_per_minute == 100

    def test_objects_pass_through_unchanged(self):
        limits = APIKeyLimits(token_per_minute=1)
        assert coerce_limits(limits) is limits


class TestUnknownKeysRaise:
    """A key that is neither a field nor a wire alias is an error, not a no-op."""

    def test_unknown_key_raises_naming_the_accepted_fields(self):
        with pytest.raises(ValidationError) as excinfo:
            coerce_limits({"tokens_per_minute": 100})

        message = str(excinfo.value)
        assert "tokens_per_minute" in message
        for accepted in (
            "token_per_minute",
            "token_per_day",
            "request_per_minute",
            "request_per_day",
            "model",
            "token_type",
        ):
            assert accepted in message

    def test_unknown_key_raises_on_assignment(self):
        key = APIKey(name="Test Key")
        with pytest.raises(ValidationError, match="Unknown limit field"):
            key.asset_limits = [{"model": "m1", "tokens_per_min": 100}]

    def test_every_unknown_key_is_named_at_once(self):
        """Reporting one at a time would make a three-typo dict a three-run fix."""
        with pytest.raises(ValidationError) as excinfo:
            coerce_limits({"tpm_": 1, "rpd_": 2})

        assert "rpd_" in str(excinfo.value) and "tpm_" in str(excinfo.value)

    def test_a_non_dict_raises(self):
        with pytest.raises(ValidationError, match="APIKeyLimits or a dict"):
            coerce_limits(42)

    def test_a_single_limit_where_a_list_is_expected_raises_clearly(self):
        """A bare dict iterates as its keys, which would produce nonsense."""
        with pytest.raises(ValidationError, match="must be a list of limits"):
            coerce_limits_list({"model": "m1", "token_per_minute": 5})


class TestTokenTypeStrings:
    """``token_type`` takes "input" / "output" / "total" as well as the enum."""

    @pytest.mark.parametrize("value", ["input", "output", "total"])
    def test_string_token_types_are_accepted(self, value):
        assert APIKeyLimits(token_type=value).token_type is TokenType(value)

    def test_string_token_type_on_assignment(self):
        """Assignment must coerce too, or the value reaches the wire as a str."""
        limits = APIKeyLimits()
        limits.token_type = "total"

        assert limits.token_type is TokenType.TOTAL

    def test_enum_still_accepted(self):
        assert APIKeyLimits(token_type=TokenType.OUTPUT).token_type is TokenType.OUTPUT

    def test_unknown_token_type_names_the_accepted_values(self):
        with pytest.raises(ValidationError) as excinfo:
            APIKeyLimits(token_type="outputs")

        message = str(excinfo.value)
        assert "'input'" in message and "'output'" in message and "'total'" in message


# -- Unset is not zero --------------------------------------------------------------


class TestUnsetIsNotZero:
    """An omitted dimension must not be written as ``0``.

    Whether the backend reads ``0`` as "blocked" or "unlimited" is not settled
    here — that is the point. A dimension the caller never mentioned is left out
    of the payload, so it cannot mean either.
    """

    def test_only_the_set_dimension_is_sent(self):
        key = APIKey(id="k", name="Test Key")
        key.asset_limits = [{"model": "m1", "token_per_minute": 10000}]

        sent = key.build_save_payload()["assetsLimits"][0]

        assert sent == {"tpm": 10000, "assetId": "m1"}
        for other in ("tpd", "rpm", "rpd"):
            assert other not in sent, f"{other} was sent for a dimension the caller never set"

    def test_a_deliberate_zero_is_still_sent(self):
        """Zero has to stay expressible, or "block this dimension" is unsayable."""
        key = APIKey(id="k", name="Test Key")
        key.asset_limits = [{"model": "m1", "token_per_minute": 0}]

        assert key.build_save_payload()["assetsLimits"][0]["tpm"] == 0

    def test_global_limits_omit_unset_dimensions(self):
        key = APIKey(id="k", name="Test Key", global_limits={"request_per_minute": 60})

        assert key.build_save_payload()["globalLimits"] == {"rpm": 60}

    def test_validate_ignores_unset_dimensions(self):
        """``None < 0`` is a TypeError, so validate() has to skip unset ones."""
        limits = APIKeyLimits(token_per_minute=1)
        assert limits.validate() is None

    def test_validate_still_rejects_a_negative(self):
        with pytest.raises(ValidationError, match="Token per minute"):
            APIKeyLimits(token_per_minute=-1).validate()

    def test_to_dict_omits_unset_dimensions(self):
        """``to_dict()`` output is a valid input, so it must not invent zeros."""
        assert APIKeyLimits(token_per_minute=5).to_dict() == {"token_per_minute": 5}


# -- get() resolves three forms -----------------------------------------------------

LISTING = [
    {"id": "key1", "name": "Production", "accessKey": "abcd1111zzzz9999", "isAdmin": False},
    {"id": "key2", "name": "Staging", "accessKey": "abcd2222zzzz9999", "isAdmin": False},
]


class TestGetResolution:
    """``get()`` takes a key ID, a key value, or a name."""

    def test_get_by_id(self):
        bound = _bound(LISTING, get_response={"id": "key1", "name": "Production", "accessKey": "abcd1111zzzz9999"})

        assert bound.get("key1").id == "key1"

    def test_get_by_key_value(self):
        """What v1's ``APIKeyFactory.get`` took; a rename used to fail here."""
        bound = _bound(LISTING)

        assert bound.get("abcd2222zzzz9999").id == "key2"

    def test_get_by_name(self):
        bound = _bound(LISTING)

        assert bound.get("Staging").id == "key2"

    def test_get_errors_naming_all_three_forms(self):
        bound = _bound(LISTING)

        with pytest.raises(ResourceError) as excinfo:
            bound.get("nothing-like-this")

        message = str(excinfo.value)
        assert "key ID" in message and "key value" in message and "key name" in message

    def test_get_does_not_echo_the_key_it_was_given(self):
        """The argument may well be a live credential; errors are often pasted."""
        bound = _bound(LISTING)

        with pytest.raises(ResourceError) as excinfo:
            bound.get("secretsecretsecret")

        assert "secretsecretsecret" not in str(excinfo.value)

    def test_duplicate_names_raise_rather_than_guess(self):
        listing = [
            {"id": "key1", "name": "Shared", "accessKey": "aaaa1111bbbb2222"},
            {"id": "key2", "name": "Shared", "accessKey": "cccc3333dddd4444"},
        ]
        bound = _bound(listing)

        with pytest.raises(ResourceError, match="are named"):
            bound.get("Shared")

    def test_a_failed_listing_surfaces_the_original_by_id_error(self):
        client = Mock()
        client.get = Mock(side_effect=APIError("the by-id failure", status_code=404))
        client.request = Mock(side_effect=RuntimeError("listing is down"))

        class BoundAPIKey(APIKey):
            context = Mock(client=client)

        with pytest.raises(APIError, match="the by-id failure"):
            BoundAPIKey.get("key1")


class TestGetDoesNotMisreportAnUnrelatedFailure:
    """A by-ID fetch that failed for its own reasons is not "no key matches".

    An expired credential or a 5xx says nothing about whether the argument was an
    ID, so reporting "No API key matches ..." sends the caller hunting for a key
    that is still there. The lookup still *runs* -- which status a backend picks
    for a non-ObjectId path segment is its business, and gating on that would
    break ``get()`` by name the day it changed -- but the real error wins once
    nothing has matched.
    """

    @pytest.mark.parametrize("status", [401, 403, 500, 502, 503])
    def test_an_unrelated_failure_wins_over_no_key_matches(self, status):
        bound = _bound(LISTING, get_error=APIError("backend said no", status_code=status))

        with pytest.raises(APIError) as excinfo:
            bound.get("nothing-like-this")

        assert excinfo.value.status_code == status
        assert "No API key matches" not in str(excinfo.value)

    @pytest.mark.parametrize("status", [401, 403, 500, 503])
    def test_the_other_two_forms_still_resolve_through_an_unrelated_failure(self, status):
        """The fallback is never gated on the status -- only the final error is.

        A backend that answers 500 for a malformed id would otherwise silently
        lose ``get()`` by name and by key value.
        """
        bound = _bound(LISTING, get_error=APIError("backend said no", status_code=status))

        assert bound.get("Staging").id == "key2"
        assert bound.get("abcd1111zzzz9999").id == "key1"

    @pytest.mark.parametrize("status", [400, 404, 422])
    def test_a_not_an_id_failure_yields_the_three_forms_message(self, status):
        """These mean "that was not an ID", so the friendly message is the answer."""
        bound = _bound(LISTING, get_error=APIError("nope", status_code=status))

        with pytest.raises(ResourceError) as excinfo:
            bound.get("nothing-like-this")

        assert "key ID" in str(excinfo.value) and "key name" in str(excinfo.value)

    def test_an_error_with_no_status_yields_the_three_forms_message(self):
        """``APIError`` defaults ``status_code`` to ``0`` for "no HTTP response".

        Falsy has to read as unknown rather than as a status outside the set, or
        a transport-level failure would be reported in place of the guidance.
        """
        for error in (APIError("connection reset"), RuntimeError("connection reset")):
            bound = _bound(LISTING, get_error=error)

            with pytest.raises(ResourceError, match="accepts a key ID"):
                bound.get("nothing-like-this")

    def test_a_surfaced_backend_error_cannot_echo_the_argument(self):
        """Why re-raising is safe: the client builds its message from the body.

        ``AixplainClient`` raises ``APIError(response.json() or response.text)``
        -- the request URL, which is what carries the caller's argument, is never
        in it. If that ever changes, this fails rather than leaking a key value.
        """
        bound = _bound(LISTING, get_error=APIError("upstream timeout", status_code=504))

        with pytest.raises(APIError) as excinfo:
            bound.get("SUPER-SECRET-KEY-VALUE")

        assert "SUPER-SECRET-KEY-VALUE" not in str(excinfo.value)


class TestKeyValueMatchingIsExact:
    """Two keys sharing their first and last four characters each resolve correctly."""

    #: Identical prefix (``abcd``) and suffix (``9999``); only the middle differs.
    COLLIDING = LISTING

    def test_first_of_a_colliding_pair(self):
        bound = _bound(self.COLLIDING)

        assert bound.get_by_access_key("abcd1111zzzz9999").id == "key1"

    def test_second_of_a_colliding_pair(self):
        """The old prefix/suffix match returned key1 here — the wrong key.

        Limits written through the returned object would have landed on a key the
        caller never named.
        """
        bound = _bound(self.COLLIDING)

        assert bound.get_by_access_key("abcd2222zzzz9999").id == "key2"

    def test_get_resolves_a_colliding_pair_too(self):
        bound = _bound(self.COLLIDING)

        assert bound.get("abcd1111zzzz9999").id == "key1"
        assert bound.get("abcd2222zzzz9999").id == "key2"

    def test_a_masked_listing_still_resolves_when_unambiguous(self):
        """Backends that mask the key leave only the prefix and suffix to go on."""
        bound = _bound([{"id": "key1", "name": "Production", "accessKey": "abcd...9999"}])

        assert bound.get_by_access_key("abcd1111zzzz9999").id == "key1"

    def test_an_ambiguous_masked_listing_raises_instead_of_guessing(self):
        listing = [
            {"id": "key1", "name": "Production", "accessKey": "abcd...9999"},
            {"id": "key2", "name": "Staging", "accessKey": "abcd...9999"},
        ]
        bound = _bound(listing)

        with pytest.raises(ResourceError) as excinfo:
            bound.get_by_access_key("abcd1111zzzz9999")

        assert "cannot be resolved" in str(excinfo.value)
        assert "key1" in str(excinfo.value) and "key2" in str(excinfo.value)

    def test_unknown_key_value_still_raises_not_found(self):
        bound = _bound(LISTING)

        with pytest.raises(ResourceError, match="not found"):
            bound.get_by_access_key("wxyz0000wxyz0000")

    def test_short_access_key_is_rejected(self):
        bound = _bound(LISTING)

        with pytest.raises(ValidationError, match="at least 8 characters"):
            bound.get_by_access_key("short")


# -- Importable from the package root -----------------------------------------------


def test_limits_and_token_type_import_from_the_package_root():
    """``from aixplain import APIKeyLimits, TokenType`` — no version segment."""
    from aixplain import APIKeyLimits as RootLimits, TokenType as RootTokenType

    assert RootLimits is APIKeyLimits
    assert RootTokenType is TokenType
    assert RootTokenType.OUTPUT.value == "output"
    assert RootLimits(token_per_minute=10, token_type=RootTokenType.OUTPUT).token_per_minute == 10


def test_plain_data_forms_import_from_the_package_root():
    """The TypedDict and the Literal are exported alongside what they describe."""
    import aixplain

    for name in ("APIKeyLimits", "APIKeyLimitsDict", "APIKeyUsageLimit", "TokenType", "TokenTypeValue"):
        assert name in aixplain.__all__, f"{name} is not exported from aixplain"
        assert hasattr(aixplain, name)


def test_the_typed_dict_declares_exactly_the_accepted_fields():
    """The TypedDict is what a type checker flags a typo against.

    If it drifts from what ``coerce_limits`` accepts, the checker and the runtime
    disagree — which is worse than having neither.
    """
    from aixplain import APIKeyLimitsDict
    from aixplain.v2.api_key import LIMIT_FIELDS

    assert set(APIKeyLimitsDict.__annotations__) == set(LIMIT_FIELDS)
