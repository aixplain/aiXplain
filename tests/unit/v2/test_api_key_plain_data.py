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
from unittest.mock import Mock, patch

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

        assert payload["assetsLimits"] == [
            {"tpm": 10000, "tpd": 0, "rpm": 0, "rpd": 0, "tokenType": "output", "assetId": "model1"}
        ]

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


class TestUnsetIsNotZeroInMemory:
    """An unset dimension stays ``None`` in memory, but is sent as ``0``.

    PROD-2917 asked for an unset dimension to be distinguishable from a
    deliberate ``0``. In memory it is: the field defaults to ``None``,
    ``validate()`` skips it, and ``to_dict()`` leaves it out.

    On the wire it is not, yet. The backend rejects a partial limits payload
    with a 500, so ``_limits_to_api_dict`` fills every dimension the caller did
    not set with ``0`` -- exactly the payload shipped before 0.3.0. Sending a
    partial payload is what the follow-up covers, and it needs a backend change
    first; the SDK cannot deliver it alone.
    """

    def test_every_dimension_is_sent_even_when_unset(self):
        """A partial payload 500s, so the wire carries all four dimensions."""
        key = APIKey(id="k", name="Test Key")
        key.asset_limits = [{"model": "m1", "token_per_minute": 10000}]

        sent = key.build_save_payload()["assetsLimits"][0]

        assert sent == {
            "tpm": 10000,
            "tpd": 0,
            "rpm": 0,
            "rpd": 0,
            "tokenType": None,
            "assetId": "m1",
        }

    def test_a_deliberate_zero_is_still_sent(self):
        """Zero has to stay expressible, or "block this dimension" is unsayable."""
        key = APIKey(id="k", name="Test Key")
        key.asset_limits = [{"model": "m1", "token_per_minute": 0}]

        assert key.build_save_payload()["assetsLimits"][0]["tpm"] == 0

    def test_global_limits_also_send_every_dimension(self):
        key = APIKey(id="k", name="Test Key", global_limits={"request_per_minute": 60})

        assert key.build_save_payload()["globalLimits"] == {
            "tpm": 0,
            "tpd": 0,
            "rpm": 60,
            "rpd": 0,
            "tokenType": None,
        }

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

#: ObjectId-shaped ids on purpose -- ``get()`` routes an ID-shaped argument to the
#: by-ID endpoint and anything else through a listing, so a fake id like "key1"
#: would quietly exercise the wrong path.
LISTING = [
    {"id": "6414bd3cd09663e9225130e8", "name": "Production", "accessKey": "abcd1111zzzz9999", "isAdmin": False},
    {"id": "6414bd3cd09663e9225130e9", "name": "Staging", "accessKey": "abcd2222zzzz9999", "isAdmin": False},
]
KEY1 = LISTING[0]["id"]
KEY2 = LISTING[1]["id"]


class TestGetResolution:
    """``get()`` takes a key ID, a key value, or a name."""

    def test_get_by_id(self):
        bound = _bound(LISTING, get_response=dict(LISTING[0]))

        assert bound.get(KEY1).id == KEY1

    def test_get_by_key_value(self):
        """What v1's ``APIKeyFactory.get`` took; a rename used to fail here."""
        bound = _bound(LISTING)

        assert bound.get("abcd2222zzzz9999").id == KEY2

    def test_get_by_name(self):
        bound = _bound(LISTING)

        assert bound.get("Staging").id == KEY2

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
            {"id": KEY1, "name": "Shared", "accessKey": "aaaa1111bbbb2222"},
            {"id": KEY2, "name": "Shared", "accessKey": "cccc3333dddd4444"},
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

        # ID-shaped, so the by-ID fetch runs first and its failure is the one
        # worth reporting when the listing fallback also fails.
        with pytest.raises(APIError, match="the by-id failure"):
            BoundAPIKey.get("6414bd3cd09663e9225130e8")


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

        assert bound.get("Staging").id == KEY2
        assert bound.get("abcd1111zzzz9999").id == KEY1

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

        assert bound.get_by_access_key("abcd1111zzzz9999").id == KEY1

    def test_second_of_a_colliding_pair(self):
        """The old prefix/suffix match returned key1 here — the wrong key.

        Limits written through the returned object would have landed on a key the
        caller never named.
        """
        bound = _bound(self.COLLIDING)

        assert bound.get_by_access_key("abcd2222zzzz9999").id == KEY2

    def test_get_resolves_a_colliding_pair_too(self):
        bound = _bound(self.COLLIDING)

        assert bound.get("abcd1111zzzz9999").id == KEY1
        assert bound.get("abcd2222zzzz9999").id == KEY2

    def test_a_masked_listing_still_resolves_when_unambiguous(self):
        """Backends that mask the key leave only the prefix and suffix to go on."""
        bound = _bound([{"id": KEY1, "name": "Production", "accessKey": "abcd...9999"}])

        assert bound.get_by_access_key("abcd1111zzzz9999").id == KEY1

    def test_an_ambiguous_masked_listing_raises_instead_of_guessing(self):
        listing = [
            {"id": KEY1, "name": "Production", "accessKey": "abcd...9999"},
            {"id": KEY2, "name": "Staging", "accessKey": "abcd...9999"},
        ]
        bound = _bound(listing)

        with pytest.raises(ResourceError) as excinfo:
            bound.get_by_access_key("abcd1111zzzz9999")

        assert "cannot be resolved" in str(excinfo.value)
        assert KEY1 in str(excinfo.value) and KEY2 in str(excinfo.value)

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


class TestGetKeepsSecretsOutOfRequestUrls:
    """A key value must never become a URL path segment.

    ``get()`` invites a key value by contract, and the by-ID endpoint puts its
    argument in the path -- where access logs, proxies and error-tracking
    breadcrumbs record it. So only an ID-shaped argument is sent there; anything
    else is resolved from a listing, and reaches the by-ID endpoint only once the
    listing has established it is not a key on this account.
    """

    @staticmethod
    def _recording_bound(listing):
        """An APIKey bound to a client that records every path it is asked for."""
        paths = []

        def get(path, **kwargs):
            paths.append(path)
            if path == APIKey.RESOURCE_PATH:
                return listing
            raise APIError(f"Not found: {path}", status_code=404)

        def request(method, path, **kwargs):
            paths.append(path)
            return listing

        client = Mock()
        client.get = Mock(side_effect=get)
        client.request = Mock(side_effect=request)

        class BoundAPIKey(APIKey):
            context = Mock(client=client)

        return BoundAPIKey, paths

    def test_a_key_value_never_reaches_a_url(self):
        secret = "abcd1111zzzz9999"
        bound, paths = self._recording_bound(LISTING)

        assert bound.get(secret).id == KEY1
        assert not any(secret in path for path in paths), f"the key value reached a URL: {paths}"

    def test_a_name_never_reaches_a_url(self):
        """Names are not secret, but they are also not ids -- same path either way."""
        bound, paths = self._recording_bound(LISTING)

        assert bound.get("Staging").id == KEY2
        assert paths == [APIKey.RESOURCE_PATH]

    def test_an_id_shaped_argument_still_goes_straight_to_the_by_id_endpoint(self):
        """The common case must not pay for a listing, or pull every key's value.

        ``APIKey.list()`` returns the access key of every key on the account, so
        routing an ordinary by-ID fetch through it would be its own exposure.
        """
        bound, paths = self._recording_bound(LISTING)
        bound._resolve_from_listing = Mock(return_value=None)

        client_get = bound.context.client.get
        client_get.side_effect = lambda path, **kwargs: dict(LISTING[0])

        assert bound.get(KEY1).id == KEY1
        assert paths == [] or paths == [f"{APIKey.RESOURCE_PATH}/{KEY1}"]

    def test_a_non_id_argument_absent_from_the_listing_still_tries_by_id(self):
        """A key the listing omits must remain reachable by its id."""
        bound, paths = self._recording_bound([])

        with pytest.raises(ResourceError, match="accepts a key ID"):
            bound.get("not-a-key")

        assert f"{APIKey.RESOURCE_PATH}/not-a-key" in paths


class TestGetResolutionOrder:
    """Exact matches win over the masked-key guess."""

    def test_an_exact_name_beats_a_masked_key_coincidence(self):
        """A name is an equality test; a masked key match is, by design, a guess."""
        listing = [
            {"id": KEY1, "name": "Production", "accessKey": "XXXXmiddleYYYY"},
            {"id": KEY2, "name": "XXXXotherYYYY", "accessKey": "zzzz"},
        ]
        bound = _bound(listing)

        assert bound.get("XXXXotherYYYY").id == KEY2

    def test_the_masked_guess_keeps_its_eight_character_floor(self):
        """Below 8 characters the prefix and suffix overlap and match anything.

        ``get_by_access_key`` enforces the floor up front; ``get()`` reaches the
        same helper with arbitrary strings, so the floor lives in the helper too.
        """
        bound = _bound([{"id": KEY1, "name": "Production", "accessKey": "keyXXXXkey"}])

        with pytest.raises(ResourceError, match="accepts a key ID"):
            bound.get("key")

    def test_an_id_in_the_listing_resolves_even_when_not_object_id_shaped(self):
        """The shape test is a routing hint, not a contract on what an id may be."""
        bound = _bound([{"id": "legacy-style-id", "name": "Legacy", "accessKey": "aaaa1111bbbb2222"}])

        assert bound.get("legacy-style-id").id == "legacy-style-id"

    def test_kwargs_reach_the_listing_fallback(self):
        """The docstring promises kwargs are forwarded; the fallback dropped them."""
        bound = _bound(LISTING)
        with patch.object(bound, "list", wraps=bound.list) as listed:
            bound.get("Staging", api_key="scoped")

        assert listed.call_args.kwargs.get("api_key") == "scoped"
