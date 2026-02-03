"""Functional tests for v2 API key management with TokenType support."""

import pytest

from aixplain.v2 import APIKey, APIKeyLimits, APIKeyUsageLimit, TokenType


class TestAPIKeyBasicOperations:
    """Test basic API key operations."""

    def test_list_api_keys(self, client):
        """Test listing all API keys."""
        api_keys = client.APIKey.list()

        assert isinstance(api_keys, list)
        for api_key in api_keys:
            assert isinstance(api_key, APIKey)
            assert api_key.id is not None

    def test_list_api_keys_parses_token_type(self, client):
        """Test that list() correctly parses token_type from API response."""
        api_keys = client.APIKey.list()

        assert isinstance(api_keys, list)
        # Verify token_type is parsed correctly (either None or a TokenType enum)
        for api_key in api_keys:
            if api_key.global_limits and api_key.global_limits.token_type is not None:
                assert isinstance(api_key.global_limits.token_type, TokenType)
            for asset_limit in api_key.asset_limits:
                if asset_limit.token_type is not None:
                    assert isinstance(asset_limit.token_type, TokenType)
