"""Unit tests for the v2 API key management module.

This module tests the API key classes and rate limit management
functionality in the v2 SDK.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta, timezone

from aixplain.v2.api_key import (
    APIKey,
    APIKeyLimits,
    APIKeyUsageLimit,
    TokenType,
)
from aixplain.v2.exceptions import ResourceError, ValidationError


# =============================================================================
# TokenType Enum Tests
# =============================================================================


class TestTokenType:
    """Tests for TokenType enum."""

    def test_token_type_input(self):
        """INPUT token type should have correct value."""
        assert TokenType.INPUT.value == "input"

    def test_token_type_output(self):
        """OUTPUT token type should have correct value."""
        assert TokenType.OUTPUT.value == "output"

    def test_token_type_total(self):
        """TOTAL token type should have correct value."""
        assert TokenType.TOTAL.value == "total"

    def test_token_type_from_string(self):
        """TokenType should be creatable from string."""
        assert TokenType("input") == TokenType.INPUT
        assert TokenType("output") == TokenType.OUTPUT
        assert TokenType("total") == TokenType.TOTAL

    def test_token_type_invalid_string_raises_error(self):
        """TokenType should raise ValueError for invalid strings."""
        with pytest.raises(ValueError):
            TokenType("invalid")


# =============================================================================
# APIKeyLimits Tests
# =============================================================================


class TestAPIKeyLimits:
    """Tests for APIKeyLimits class."""

    def test_create_limits_with_defaults(self):
        """Limits should have default values of 0."""
        limits = APIKeyLimits()

        assert limits.token_per_minute == 0
        assert limits.token_per_day == 0
        assert limits.request_per_minute == 0
        assert limits.request_per_day == 0
        assert limits.model_id is None
        assert limits.token_type is None

    def test_create_limits_with_values(self):
        """Limits should accept custom values."""
        limits = APIKeyLimits(
            token_per_minute=100,
            token_per_day=1000,
            request_per_minute=10,
            request_per_day=100,
            model_id="model123",
            token_type=TokenType.INPUT,
        )

        assert limits.token_per_minute == 100
        assert limits.token_per_day == 1000
        assert limits.request_per_minute == 10
        assert limits.request_per_day == 100
        assert limits.model_id == "model123"
        assert limits.token_type == TokenType.INPUT

    def test_limits_validate_success(self):
        """validate() should pass for valid limits."""
        limits = APIKeyLimits(
            token_per_minute=100,
            token_per_day=1000,
            request_per_minute=10,
            request_per_day=100,
        )

        limits.validate()  # Should not raise

    def test_limits_validate_negative_token_per_minute(self):
        """validate() should fail for negative token_per_minute."""
        limits = APIKeyLimits(token_per_minute=-1)

        with pytest.raises(ValidationError, match="Token per minute must be >= 0"):
            limits.validate()

    def test_limits_validate_negative_token_per_day(self):
        """validate() should fail for negative token_per_day."""
        limits = APIKeyLimits(token_per_day=-1)

        with pytest.raises(ValidationError, match="Token per day must be >= 0"):
            limits.validate()

    def test_limits_validate_negative_request_per_minute(self):
        """validate() should fail for negative request_per_minute."""
        limits = APIKeyLimits(request_per_minute=-1)

        with pytest.raises(ValidationError, match="Request per minute must be >= 0"):
            limits.validate()

    def test_limits_validate_negative_request_per_day(self):
        """validate() should fail for negative request_per_day."""
        limits = APIKeyLimits(request_per_day=-1)

        with pytest.raises(ValidationError, match="Request per day must be >= 0"):
            limits.validate()

    def test_limits_post_init_parses_string_token_type(self):
        """__post_init__ should parse string token_type."""
        limits = APIKeyLimits(token_type="input")

        assert limits.token_type == TokenType.INPUT

    def test_limits_from_dict(self):
        """from_dict() should parse API response format."""
        data = {
            "tpm": 100,
            "tpd": 1000,
            "rpm": 10,
            "rpd": 100,
            "assetId": "model123",
            "tokenType": "input",
        }

        limits = APIKeyLimits.from_dict(data)

        assert limits.token_per_minute == 100
        assert limits.token_per_day == 1000
        assert limits.request_per_minute == 10
        assert limits.request_per_day == 100
        assert limits.model_id == "model123"
        assert limits.token_type == TokenType.INPUT

    def test_limits_from_dict_output_token_type(self):
        """from_dict() should parse OUTPUT token type."""
        data = {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100, "tokenType": "output"}

        limits = APIKeyLimits.from_dict(data)

        assert limits.token_type == TokenType.OUTPUT

    def test_limits_from_dict_total_token_type(self):
        """from_dict() should parse TOTAL token type."""
        data = {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100, "tokenType": "total"}

        limits = APIKeyLimits.from_dict(data)

        assert limits.token_type == TokenType.TOTAL

    def test_limits_from_dict_null_token_type(self):
        """from_dict() should handle null tokenType."""
        data = {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100, "tokenType": None}

        limits = APIKeyLimits.from_dict(data)

        assert limits.token_type is None


# =============================================================================
# APIKeyUsageLimit Tests
# =============================================================================


class TestAPIKeyUsageLimit:
    """Tests for APIKeyUsageLimit class."""

    def test_create_usage_limit_with_defaults(self):
        """Usage limits should have default values of None."""
        usage = APIKeyUsageLimit()

        assert usage.daily_request_count is None
        assert usage.daily_request_limit is None
        assert usage.daily_token_count is None
        assert usage.daily_token_limit is None
        assert usage.model_id is None

    def test_create_usage_limit_with_values(self):
        """Usage limits should accept custom values."""
        usage = APIKeyUsageLimit(
            daily_request_count=50,
            daily_request_limit=100,
            daily_token_count=500,
            daily_token_limit=1000,
            model_id="model123",
        )

        assert usage.daily_request_count == 50
        assert usage.daily_request_limit == 100
        assert usage.daily_token_count == 500
        assert usage.daily_token_limit == 1000
        assert usage.model_id == "model123"

    def test_usage_limit_from_dict(self):
        """from_dict() should parse API response format."""
        data = {
            "requestCount": 50,
            "requestCountLimit": 100,
            "tokenCount": 500,
            "tokenCountLimit": 1000,
            "assetId": "model123",
        }

        usage = APIKeyUsageLimit.from_dict(data)

        assert usage.daily_request_count == 50
        assert usage.daily_request_limit == 100
        assert usage.daily_token_count == 500
        assert usage.daily_token_limit == 1000
        assert usage.model_id == "model123"


# =============================================================================
# APIKey Tests
# =============================================================================


class TestAPIKey:
    """Tests for APIKey class."""

    def test_create_api_key_basic(self):
        """Should create APIKey with basic attributes."""
        api_key = APIKey(
            id="key123",
            name="Test Key",
            budget=1000.0,
        )

        assert api_key.id == "key123"
        assert api_key.name == "Test Key"
        assert api_key.budget == 1000.0

    def test_create_api_key_with_global_limits(self):
        """Should create APIKey with global limits."""
        global_limits = APIKeyLimits(token_per_minute=100, token_per_day=1000)

        api_key = APIKey(
            name="Test Key",
            global_limits=global_limits,
        )

        assert api_key.global_limits is not None
        assert api_key.global_limits.token_per_minute == 100

    def test_create_api_key_with_asset_limits(self):
        """Should create APIKey with asset limits."""
        asset_limits = [
            APIKeyLimits(token_per_minute=100, model_id="model1"),
            APIKeyLimits(token_per_minute=200, model_id="model2"),
        ]

        api_key = APIKey(
            name="Test Key",
            asset_limits=asset_limits,
        )

        assert len(api_key.asset_limits) == 2
        assert api_key.asset_limits[0].model_id == "model1"

    def test_api_key_from_dict_parses_nested_limits(self):
        """from_dict() should parse nested limits using dataclass_json."""
        data = {
            "id": "key123",
            "name": "Test Key",
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100},
            "assetsLimits": [{"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1"}],
        }

        api_key = APIKey.from_dict(data)

        assert api_key.global_limits is not None
        assert api_key.global_limits.token_per_minute == 100
        assert len(api_key.asset_limits) == 1
        assert api_key.asset_limits[0].model_id == "model1"

    def test_api_key_validate_success(self):
        """_validate_limits() should pass for valid API key."""
        api_key = APIKey(
            name="Test Key",
            budget=1000.0,
            global_limits=APIKeyLimits(token_per_minute=100),
            asset_limits=[APIKeyLimits(token_per_minute=50, model_id="model1")],
        )

        api_key._validate_limits()  # Should not raise

    def test_api_key_validate_negative_budget(self):
        """_validate_limits() should fail for negative budget."""
        api_key = APIKey(
            name="Test Key",
            budget=-100.0,
        )

        with pytest.raises(ValidationError, match="Budget must be >= 0"):
            api_key._validate_limits()

    def test_api_key_validate_asset_without_model_id(self):
        """_validate_limits() should fail if asset limit has no model_id."""
        api_key = APIKey(
            name="Test Key",
            asset_limits=[APIKeyLimits(token_per_minute=50)],  # No model_id
        )

        with pytest.raises(ValidationError, match="must have a model_id"):
            api_key._validate_limits()

    def test_api_key_build_save_payload(self):
        """build_save_payload() should create correct payload."""
        api_key = APIKey(
            id="key123",
            name="Test Key",
            budget=1000.0,
            global_limits=APIKeyLimits(
                token_per_minute=100,
                token_per_day=1000,
                request_per_minute=10,
                request_per_day=100,
            ),
            asset_limits=[
                APIKeyLimits(
                    token_per_minute=50,
                    token_per_day=500,
                    request_per_minute=5,
                    request_per_day=50,
                    model_id="model1",
                )
            ],
            expires_at="2024-12-31T23:59:59.000000Z",
        )

        payload = api_key.build_save_payload()

        assert payload["id"] == "key123"
        assert payload["name"] == "Test Key"
        assert payload["budget"] == 1000.0
        assert payload["globalLimits"]["tpm"] == 100
        assert len(payload["assetsLimits"]) == 1
        assert payload["assetsLimits"][0]["assetId"] == "model1"

    def test_api_key_build_save_payload_datetime_expires_at(self):
        """build_save_payload() should format datetime expires_at."""
        expires = datetime(2024, 12, 31, 23, 59, 59, 123456)
        api_key = APIKey(
            name="Test Key",
            expires_at=expires,
        )

        payload = api_key.build_save_payload()

        assert "2024-12-31" in payload["expiresAt"]

    def test_api_key_build_save_payload_with_global_token_type(self):
        """build_save_payload() should include tokenType in global limits."""
        api_key = APIKey(
            name="Test Key",
            budget=1000.0,
            global_limits=APIKeyLimits(
                token_per_minute=100,
                token_per_day=1000,
                request_per_minute=10,
                request_per_day=100,
                token_type=TokenType.OUTPUT,
            ),
        )

        payload = api_key.build_save_payload()

        assert payload["globalLimits"]["tokenType"] == "output"

    def test_api_key_build_save_payload_with_asset_token_type(self):
        """build_save_payload() should include tokenType in asset limits."""
        api_key = APIKey(
            name="Test Key",
            budget=1000.0,
            asset_limits=[
                APIKeyLimits(
                    token_per_minute=100,
                    token_per_day=1000,
                    request_per_minute=10,
                    request_per_day=100,
                    model_id="model1",
                    token_type=TokenType.TOTAL,
                ),
            ],
        )

        payload = api_key.build_save_payload()

        assert payload["assetsLimits"][0]["tokenType"] == "total"

    def test_api_key_repr(self):
        """__repr__ should return readable string."""
        api_key = APIKey(id="key123", name="Test Key")

        repr_str = repr(api_key)

        assert "key123" in repr_str
        assert "Test Key" in repr_str

    def test_api_key_set_token_per_day_global(self):
        """set_token_per_day() should update global limits."""
        api_key = APIKey(
            name="Test Key",
            global_limits=APIKeyLimits(token_per_day=100),
        )

        api_key.set_token_per_day(200)

        assert api_key.global_limits.token_per_day == 200

    def test_api_key_set_token_per_day_creates_global_limits(self):
        """set_token_per_day() should create global limits if None."""
        api_key = APIKey(name="Test Key")

        api_key.set_token_per_day(200)

        assert api_key.global_limits is not None
        assert api_key.global_limits.token_per_day == 200

    def test_api_key_set_token_per_day_model(self):
        """set_token_per_day() should update asset limits for model."""
        api_key = APIKey(
            name="Test Key",
            asset_limits=[APIKeyLimits(token_per_day=100, model_id="model1")],
        )

        api_key.set_token_per_day(200, model_id="model1")

        assert api_key.asset_limits[0].token_per_day == 200

    def test_api_key_set_token_per_day_model_not_found(self):
        """set_token_per_day() should raise for unknown model."""
        api_key = APIKey(
            name="Test Key",
            asset_limits=[APIKeyLimits(token_per_day=100, model_id="model1")],
        )

        with pytest.raises(ResourceError, match="not found"):
            api_key.set_token_per_day(200, model_id="unknown_model")

    def test_api_key_set_token_per_minute(self):
        """set_token_per_minute() should update limits."""
        api_key = APIKey(name="Test Key", global_limits=APIKeyLimits())

        api_key.set_token_per_minute(500)

        assert api_key.global_limits.token_per_minute == 500

    def test_api_key_set_request_per_day(self):
        """set_request_per_day() should update limits."""
        api_key = APIKey(name="Test Key", global_limits=APIKeyLimits())

        api_key.set_request_per_day(1000)

        assert api_key.global_limits.request_per_day == 1000

    def test_api_key_set_request_per_minute(self):
        """set_request_per_minute() should update limits."""
        api_key = APIKey(name="Test Key", global_limits=APIKeyLimits())

        api_key.set_request_per_minute(100)

        assert api_key.global_limits.request_per_minute == 100

    def test_api_key_limits_to_dict_static_method(self):
        """_limits_to_dict() static method should convert limits properly."""
        limits = APIKeyLimits(
            token_per_minute=100,
            token_per_day=1000,
            request_per_minute=10,
            request_per_day=100,
            token_type=TokenType.INPUT,
        )

        result = APIKey._limits_to_dict(limits)

        assert result == {
            "tpm": 100,
            "tpd": 1000,
            "rpm": 10,
            "rpd": 100,
            "tokenType": "input",
        }

    def test_api_key_limits_to_dict_with_model_id(self):
        """_limits_to_dict() should include model_id when flag is set."""
        limits = APIKeyLimits(token_per_minute=100, model_id="model1")

        result = APIKey._limits_to_dict(limits, include_model_id=True)

        assert result["assetId"] == "model1"

    def test_api_key_limits_to_dict_output_token_type(self):
        """_limits_to_dict() should serialize OUTPUT token type."""
        limits = APIKeyLimits(
            token_per_minute=100,
            token_per_day=1000,
            request_per_minute=10,
            request_per_day=100,
            token_type=TokenType.OUTPUT,
        )

        result = APIKey._limits_to_dict(limits)

        assert result["tokenType"] == "output"

    def test_api_key_limits_to_dict_total_token_type(self):
        """_limits_to_dict() should serialize TOTAL token type."""
        limits = APIKeyLimits(
            token_per_minute=100,
            token_per_day=1000,
            request_per_minute=10,
            request_per_day=100,
            token_type=TokenType.TOTAL,
        )

        result = APIKey._limits_to_dict(limits)

        assert result["tokenType"] == "total"

    def test_api_key_limits_to_dict_none_token_type(self):
        """_limits_to_dict() should serialize None token_type as None."""
        limits = APIKeyLimits(
            token_per_minute=100,
            token_per_day=1000,
            request_per_minute=10,
            request_per_day=100,
            token_type=None,
        )

        result = APIKey._limits_to_dict(limits)

        assert result["tokenType"] is None

    def test_api_key_parse_limits_static_method(self):
        """_parse_limits() static method should parse dicts and pass through objects."""
        # Parse dict
        parsed = APIKey._parse_limits({"tpm": 100, "tpd": 1000})
        assert isinstance(parsed, APIKeyLimits)
        assert parsed.token_per_minute == 100

        # Pass through existing object
        limits = APIKeyLimits(token_per_minute=200)
        parsed = APIKey._parse_limits(limits)
        assert parsed is limits

        # Handle None
        parsed = APIKey._parse_limits(None)
        assert parsed is None


# =============================================================================
# APIKey List Tests (SearchResourceMixin)
# =============================================================================


class TestAPIKeyList:
    """Tests for APIKey list functionality via SearchResourceMixin."""

    def test_api_key_list_returns_list(self):
        """list() should return list of APIKey objects."""
        response_data = [
            {"id": "key1", "name": "Key 1", "accessKey": "abc...xyz", "isAdmin": False},
            {"id": "key2", "name": "Key 2", "accessKey": "def...uvw", "isAdmin": True},
        ]

        mock_client = Mock()
        mock_client.request = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_keys = MockAPIKey.list()

        assert isinstance(api_keys, list)
        assert len(api_keys) == 2
        assert api_keys[0].id == "key1"
        assert api_keys[1].id == "key2"
        # Verify it uses GET method with empty filters (configured via class attrs)
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "get"  # PAGINATE_METHOD
        assert call_args[0][1] == "sdk/api-keys"  # RESOURCE_PATH with empty PAGINATE_PATH

    def test_api_key_list_parses_nested_limits(self):
        """list() should parse globalLimits and assetsLimits via from_dict."""
        response_data = [
            {
                "id": "key1",
                "name": "Key 1",
                "accessKey": "abc...xyz",
                "isAdmin": False,
                "globalLimits": {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100},
                "assetsLimits": [{"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1"}],
            }
        ]

        mock_client = Mock()
        mock_client.request = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_keys = MockAPIKey.list()

        assert api_keys[0].global_limits is not None
        assert api_keys[0].global_limits.token_per_minute == 100
        assert len(api_keys[0].asset_limits) == 1
        assert api_keys[0].asset_limits[0].model_id == "model1"

    def test_api_key_list_parses_token_type(self):
        """list() should parse tokenType from API response."""
        response_data = [
            {
                "id": "key1",
                "name": "Key 1",
                "accessKey": "abc...xyz",
                "isAdmin": False,
                "globalLimits": {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100, "tokenType": "output"},
                "assetsLimits": [
                    {"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1", "tokenType": "input"}
                ],
            }
        ]

        mock_client = Mock()
        mock_client.request = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_keys = MockAPIKey.list()

        assert api_keys[0].global_limits.token_type == TokenType.OUTPUT
        assert api_keys[0].asset_limits[0].token_type == TokenType.INPUT

    def test_api_key_search_returns_page_with_correct_page_total(self):
        """search() should return Page with page_total=1 for non-paginated endpoint."""
        response_data = [
            {"id": "key1", "name": "Key 1"},
            {"id": "key2", "name": "Key 2"},
        ]

        mock_client = Mock()
        mock_client.request = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        page = MockAPIKey.search()

        assert page.page_total == 1  # Fixed by _build_page override
        assert page.total == 2
        assert len(page.results) == 2


# =============================================================================
# APIKey Get Tests (GetResourceMixin)
# =============================================================================


class TestAPIKeyGet:
    """Tests for APIKey get functionality via GetResourceMixin."""

    def test_api_key_get_returns_api_key(self):
        """get() should return APIKey object."""
        response_data = {
            "id": "key123",
            "name": "Test Key",
            "accessKey": "abc...xyz",
            "isAdmin": False,
            "budget": 1000.0,
        }

        mock_client = Mock()
        mock_client.get = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_key = MockAPIKey.get("key123")

        assert isinstance(api_key, APIKey)
        assert api_key.id == "key123"
        assert api_key.name == "Test Key"
        assert api_key.budget == 1000.0
        mock_client.get.assert_called_once_with("sdk/api-keys/key123")

    def test_api_key_get_parses_nested_limits(self):
        """get() should parse nested limits via from_dict."""
        response_data = {
            "id": "key123",
            "name": "Test Key",
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100},
            "assetsLimits": [{"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1"}],
        }

        mock_client = Mock()
        mock_client.get = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_key = MockAPIKey.get("key123")

        assert api_key.global_limits is not None
        assert api_key.global_limits.token_per_minute == 100
        assert len(api_key.asset_limits) == 1

    def test_api_key_get_parses_token_type(self):
        """get() should parse tokenType from API response."""
        response_data = {
            "id": "key123",
            "name": "Test Key",
            "globalLimits": {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100, "tokenType": "total"},
            "assetsLimits": [{"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1", "tokenType": "output"}],
        }

        mock_client = Mock()
        mock_client.get = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_key = MockAPIKey.get("key123")

        assert api_key.global_limits.token_type == TokenType.TOTAL
        assert api_key.asset_limits[0].token_type == TokenType.OUTPUT


# =============================================================================
# APIKey Delete Tests (DeleteResourceMixin)
# =============================================================================


class TestAPIKeyDelete:
    """Tests for APIKey delete functionality via DeleteResourceMixin."""

    def test_api_key_delete_marks_deleted(self):
        """delete() should mark API key as deleted."""
        mock_client = Mock()
        mock_client.request_raw = Mock(return_value=Mock())

        api_key = APIKey(id="key123", name="Test Key")
        api_key.context = Mock(client=mock_client)

        api_key.delete()

        assert api_key.is_deleted is True
        assert api_key.id is None
        mock_client.request_raw.assert_called_once_with("delete", "sdk/api-keys/key123")


# =============================================================================
# APIKey Save Tests (BaseResource)
# =============================================================================


class TestAPIKeySave:
    """Tests for APIKey save functionality via BaseResource."""

    def test_api_key_save_creates_new(self):
        """save() should create new API key when id is None."""
        mock_client = Mock()
        mock_client.request = Mock(
            return_value={
                "id": "new_key_id",
                "name": "Test Key",
                "accessKey": "abc...xyz",
                "isAdmin": False,
            }
        )

        api_key = APIKey(
            name="Test Key",
            budget=1000.0,
            global_limits=APIKeyLimits(
                token_per_minute=100,
                token_per_day=1000,
                request_per_minute=10,
                request_per_day=100,
            ),
        )
        api_key.context = Mock(client=mock_client)

        api_key.save()

        assert api_key.id == "new_key_id"
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "post"  # BaseResource uses lowercase

    def test_api_key_save_updates_existing(self):
        """save() should update existing API key when id is set."""
        mock_client = Mock()
        mock_client.request = Mock(
            return_value={
                "id": "existing_key",
                "name": "Test Key",
                "globalLimits": {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100},
            }
        )

        api_key = APIKey(
            id="existing_key",
            name="Test Key",
            budget=1000.0,
        )
        api_key.context = Mock(client=mock_client)

        api_key.save()

        assert api_key.id == "existing_key"
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[0][0] == "PUT"  # Our _update override uses uppercase

    def test_api_key_update_populates_from_response(self):
        """_update() should populate instance from response."""
        mock_client = Mock()
        mock_client.request = Mock(
            return_value={
                "id": "existing_key",
                "name": "Updated Name",
                "globalLimits": {"tpm": 200, "tpd": 2000, "rpm": 20, "rpd": 200},
            }
        )

        api_key = APIKey(
            id="existing_key",
            name="Original Name",
        )
        api_key.context = Mock(client=mock_client)

        api_key.save()

        assert api_key.name == "Updated Name"
        assert api_key.global_limits is not None
        assert api_key.global_limits.token_per_minute == 200


# =============================================================================
# APIKey Usage Tests (API-specific endpoints)
# =============================================================================


class TestAPIKeyUsage:
    """Tests for APIKey usage functionality."""

    def test_get_usage_returns_usage_limits(self):
        """get_usage() should return list of APIKeyUsageLimit objects."""
        mock_client = Mock()
        mock_client.get = Mock(
            return_value=[
                {
                    "requestCount": 50,
                    "requestCountLimit": 100,
                    "tokenCount": 500,
                    "tokenCountLimit": 1000,
                },
                {
                    "requestCount": 25,
                    "requestCountLimit": 50,
                    "tokenCount": 250,
                    "tokenCountLimit": 500,
                    "assetId": "model1",
                },
            ]
        )

        api_key = APIKey(id="key123", name="Test Key")
        api_key.context = Mock(client=mock_client)

        usage_limits = api_key.get_usage()

        assert len(usage_limits) == 2
        assert isinstance(usage_limits[0], APIKeyUsageLimit)
        assert usage_limits[0].daily_request_count == 50
        assert usage_limits[1].model_id == "model1"

    def test_get_usage_filters_by_model_id(self):
        """get_usage() should filter by model_id."""
        mock_client = Mock()
        mock_client.get = Mock(
            return_value=[
                {
                    "requestCount": 50,
                    "requestCountLimit": 100,
                    "tokenCount": 500,
                    "tokenCountLimit": 1000,
                },
                {
                    "requestCount": 25,
                    "requestCountLimit": 50,
                    "tokenCount": 250,
                    "tokenCountLimit": 500,
                    "assetId": "model1",
                },
            ]
        )

        api_key = APIKey(id="key123", name="Test Key")
        api_key.context = Mock(client=mock_client)

        usage_limits = api_key.get_usage(model_id="model1")

        assert len(usage_limits) == 1
        assert usage_limits[0].model_id == "model1"

    def test_get_usage_limits_class_method(self):
        """get_usage_limits() class method should return usage limits."""
        mock_client = Mock()
        mock_client.get = Mock(
            return_value=[
                {
                    "requestCount": 50,
                    "requestCountLimit": 100,
                    "tokenCount": 500,
                    "tokenCountLimit": 1000,
                }
            ]
        )

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        usage_limits = MockAPIKey.get_usage_limits()

        assert len(usage_limits) == 1
        assert usage_limits[0].daily_request_count == 50


# =============================================================================
# APIKey Convenience Methods Tests
# =============================================================================


class TestAPIKeyConvenienceMethods:
    """Tests for APIKey convenience create/update methods."""

    def test_create_class_method(self):
        """create() should create and save API key."""
        mock_client = Mock()
        mock_client.request = Mock(
            return_value={
                "id": "new_key",
                "name": "Test Key",
                "accessKey": "abc...xyz",
                "isAdmin": False,
            }
        )

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        expires = datetime.now(timezone.utc) + timedelta(weeks=4)
        api_key = MockAPIKey.create(
            name="Test Key",
            budget=1000,
            global_limits={"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100},
            asset_limits=[{"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1"}],
            expires_at=expires,
        )

        assert api_key.id == "new_key"

    def test_create_with_token_type(self):
        """create() should support token_type in limits."""
        mock_client = Mock()
        mock_client.request = Mock(
            return_value={
                "id": "new_key",
                "name": "Test Key",
                "accessKey": "abc...xyz",
                "isAdmin": False,
                "globalLimits": {"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100, "tokenType": "output"},
                "assetsLimits": [
                    {"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1", "tokenType": "input"}
                ],
            }
        )

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_key = MockAPIKey.create(
            name="Test Key",
            budget=1000,
            global_limits={"tpm": 100, "tpd": 1000, "rpm": 10, "rpd": 100, "tokenType": "output"},
            asset_limits=[{"tpm": 50, "tpd": 500, "rpm": 5, "rpd": 50, "assetId": "model1", "tokenType": "input"}],
        )

        assert api_key.id == "new_key"
        # Verify the payload sent includes tokenType
        call_args = mock_client.request.call_args
        payload = call_args[1]["json"]
        assert payload["globalLimits"]["tokenType"] == "output"
        assert payload["assetsLimits"][0]["tokenType"] == "input"


# =============================================================================
# APIKey get_by_access_key Tests
# =============================================================================


class TestAPIKeyGetByAccessKey:
    """Tests for APIKey get_by_access_key functionality."""

    def test_get_by_access_key_finds_matching_key(self):
        """get_by_access_key() should find key matching first/last 4 chars."""
        response_data = [
            {
                "id": "key1",
                "name": "Key 1",
                "accessKey": "abcd1234efgh",
                "isAdmin": False,
            },
            {
                "id": "key2",
                "name": "Key 2",
                "accessKey": "wxyz5678uvst",
                "isAdmin": False,
            },
        ]

        mock_client = Mock()
        mock_client.request = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        api_key = MockAPIKey.get_by_access_key("abcd1234efgh")

        assert api_key.id == "key1"

    def test_get_by_access_key_raises_not_found(self):
        """get_by_access_key() should raise ResourceError if key not found."""
        response_data = [
            {
                "id": "key1",
                "name": "Key 1",
                "accessKey": "abcd1234efgh",
                "isAdmin": False,
            },
        ]

        mock_client = Mock()
        mock_client.request = Mock(return_value=response_data)

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        with pytest.raises(ResourceError, match="not found"):
            MockAPIKey.get_by_access_key("xxxx9999yyyy")

    def test_get_by_access_key_validates_length(self):
        """get_by_access_key() should raise ValidationError for short access keys."""
        mock_client = Mock()

        class MockAPIKey(APIKey):
            context = Mock(client=mock_client)

        with pytest.raises(ValidationError, match="at least 8 characters"):
            MockAPIKey.get_by_access_key("short")
