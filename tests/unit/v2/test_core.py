"""Unit tests for the v2 core Aixplain class.

This module tests the main entry point for the SDK, including
initialization, multi-instance support, and resource binding.
"""

import os
import pytest
from unittest.mock import patch, Mock

from aixplain.v2.core import Aixplain
from aixplain.v2.model import Model
from aixplain.v2.tool import Tool
from aixplain.v2.agent import Agent
from aixplain.v2.utility import Utility
from aixplain.v2.integration import Integration
from aixplain.v2.file import Resource
from aixplain.v2.inspector import Inspector


class TestAixplainInitialization:
    """Tests for Aixplain class initialization."""

    def test_aixplain_instance(self):
        """Test basic Aixplain instance creation."""
        with patch.object(Aixplain, "init_client"):
            with patch.object(Aixplain, "init_resources"):
                aixplain = Aixplain(api_key="test")
                assert aixplain is not None
                assert aixplain.api_key == "test"
                aixplain.init_client.assert_called_once()
                aixplain.init_resources.assert_called_once()

    def test_aixplain_api_key_required(self):
        """Should raise AssertionError when no API key provided."""
        # Clear the environment variable to ensure we're testing the assertion
        with patch.dict(os.environ, {}, clear=True):
            # Remove TEAM_API_KEY if it exists
            env_without_key = {k: v for k, v in os.environ.items() if k != "TEAM_API_KEY"}
            with patch.dict(os.environ, env_without_key, clear=True):
                with pytest.raises(AssertionError, match="API key is required"):
                    Aixplain(api_key=None)

    def test_aixplain_api_key_empty_string_fails(self):
        """Should raise AssertionError when API key is empty string."""
        with patch.dict(os.environ, {}, clear=True):
            env_without_key = {k: v for k, v in os.environ.items() if k != "TEAM_API_KEY"}
            with patch.dict(os.environ, env_without_key, clear=True):
                with pytest.raises(AssertionError, match="API key is required"):
                    Aixplain(api_key="")

    def test_aixplain_explicit_key_over_env(self):
        """Explicit api_key should override TEAM_API_KEY env var."""
        with patch.dict(os.environ, {"TEAM_API_KEY": "env_key"}):
            aixplain = Aixplain(api_key="explicit_key")
            assert aixplain.api_key == "explicit_key"


class TestAixplainEnvironmentVariables:
    """Tests for environment variable handling."""

    def test_aixplain_uses_env_api_key(self):
        """Should use TEAM_API_KEY from environment."""
        with patch.dict(os.environ, {"TEAM_API_KEY": "env_test_key"}):
            aixplain = Aixplain()
            assert aixplain.api_key == "env_test_key"

    def test_aixplain_uses_env_backend_url(self):
        """Should use BACKEND_URL from environment."""
        with patch.dict(
            os.environ,
            {
                "TEAM_API_KEY": "key",
                "BACKEND_URL": "https://custom-backend.com",
            },
        ):
            aixplain = Aixplain()
            assert aixplain.backend_url == "https://custom-backend.com"

    def test_aixplain_uses_env_pipeline_url(self):
        """Should use PIPELINES_RUN_URL from environment."""
        with patch.dict(
            os.environ,
            {
                "TEAM_API_KEY": "key",
                "PIPELINES_RUN_URL": "https://custom-pipeline.com",
            },
        ):
            aixplain = Aixplain()
            assert aixplain.pipeline_url == "https://custom-pipeline.com"

    def test_aixplain_uses_env_model_url(self):
        """Should use MODELS_RUN_URL from environment."""
        with patch.dict(
            os.environ,
            {
                "TEAM_API_KEY": "key",
                "MODELS_RUN_URL": "https://custom-models.com",
            },
        ):
            aixplain = Aixplain()
            assert aixplain.model_url == "https://custom-models.com"

    def test_aixplain_all_environment_variables(self):
        """Test that all environment variables are used when provided."""
        with patch.dict(
            os.environ,
            {
                "TEAM_API_KEY": "env_test_key",
                "BACKEND_URL": "https://env-backend.com",
                "PIPELINES_RUN_URL": "https://env-pipeline.com",
                "MODELS_RUN_URL": "https://env-models.com",
            },
        ):
            aixplain = Aixplain()
            assert aixplain.api_key == "env_test_key"
            assert aixplain.backend_url == "https://env-backend.com"
            assert aixplain.pipeline_url == "https://env-pipeline.com"
            assert aixplain.model_url == "https://env-models.com"


class TestAixplainDefaultUrls:
    """Tests for default URL configuration."""

    def test_default_backend_url_value(self):
        """Should use the class constant BACKEND_URL as default."""
        # Clear URL env vars
        env_vars = {"TEAM_API_KEY": "key"}
        with patch.dict(os.environ, env_vars, clear=True):
            aixplain = Aixplain(api_key="key")
            assert aixplain.backend_url == "https://platform-api.aixplain.com"
            assert aixplain.backend_url == Aixplain.BACKEND_URL

    def test_default_pipeline_url_value(self):
        """Should use the class constant PIPELINES_RUN_URL as default."""
        env_vars = {"TEAM_API_KEY": "key"}
        with patch.dict(os.environ, env_vars, clear=True):
            aixplain = Aixplain(api_key="key")
            expected = "https://platform-api.aixplain.com/assets/pipeline/execution/run"
            assert aixplain.pipeline_url == expected
            assert aixplain.pipeline_url == Aixplain.PIPELINES_RUN_URL

    def test_default_model_url_value(self):
        """Should use the class constant MODELS_RUN_URL as default."""
        env_vars = {"TEAM_API_KEY": "key"}
        with patch.dict(os.environ, env_vars, clear=True):
            aixplain = Aixplain(api_key="key")
            expected = "https://models.aixplain.com/api/v2/execute"
            assert aixplain.model_url == expected
            assert aixplain.model_url == Aixplain.MODELS_RUN_URL

    def test_explicit_backend_url_overrides_env(self):
        """Explicit backend_url parameter should override environment."""
        with patch.dict(
            os.environ,
            {
                "TEAM_API_KEY": "key",
                "BACKEND_URL": "https://env-backend.com",
            },
        ):
            aixplain = Aixplain(
                api_key="key",
                backend_url="https://explicit-backend.com",
            )
            assert aixplain.backend_url == "https://explicit-backend.com"

    def test_explicit_pipeline_url_overrides_env(self):
        """Explicit pipeline_url parameter should override environment."""
        with patch.dict(
            os.environ,
            {
                "TEAM_API_KEY": "key",
                "PIPELINES_RUN_URL": "https://env-pipeline.com",
            },
        ):
            aixplain = Aixplain(
                api_key="key",
                pipeline_url="https://explicit-pipeline.com",
            )
            assert aixplain.pipeline_url == "https://explicit-pipeline.com"

    def test_explicit_model_url_overrides_env(self):
        """Explicit model_url parameter should override environment."""
        with patch.dict(
            os.environ,
            {
                "TEAM_API_KEY": "key",
                "MODELS_RUN_URL": "https://env-model.com",
            },
        ):
            aixplain = Aixplain(
                api_key="key",
                model_url="https://explicit-model.com",
            )
            assert aixplain.model_url == "https://explicit-model.com"


class TestAixplainInitClient:
    """Tests for client initialization."""

    def test_init_client_creates_client(self):
        """init_client should create AixplainClient."""
        aixplain = Aixplain(api_key="test_key")

        with patch("aixplain.v2.core.AixplainClient") as mock_client:
            aixplain.init_client()

            mock_client.assert_called_once_with(
                base_url=aixplain.backend_url,
                team_api_key="test_key",
            )

    def test_init_client_stores_client(self):
        """init_client should store client instance."""
        aixplain = Aixplain(api_key="test")

        assert aixplain.client is not None


class TestAixplainInitResources:
    """Tests for resource initialization."""

    def test_init_resources_creates_all_resources(self):
        """init_resources should create all resource types."""
        aixplain = Aixplain(api_key="test")

        assert aixplain.Model is not None
        assert aixplain.Agent is not None
        assert aixplain.Tool is not None
        assert aixplain.Utility is not None
        assert aixplain.Integration is not None
        assert aixplain.Resource is not None
        assert aixplain.Inspector is not None

    def test_init_resources_sets_context(self):
        """All resource classes should have context set to Aixplain instance."""
        aixplain = Aixplain(api_key="test")

        assert aixplain.Model.context == aixplain
        assert aixplain.Agent.context == aixplain
        assert aixplain.Tool.context == aixplain
        assert aixplain.Utility.context == aixplain
        assert aixplain.Integration.context == aixplain
        assert aixplain.Resource.context == aixplain
        assert aixplain.Inspector.context == aixplain

    def test_init_resources_creates_subclasses(self):
        """Resource classes should be subclasses of base types."""
        aixplain = Aixplain(api_key="test")

        assert issubclass(aixplain.Model, Model)
        assert issubclass(aixplain.Agent, Agent)
        assert issubclass(aixplain.Tool, Tool)
        assert issubclass(aixplain.Utility, Utility)
        assert issubclass(aixplain.Integration, Integration)

    def test_init_resources_creates_unique_classes(self):
        """Each instance should have unique resource classes (not base types)."""
        aixplain = Aixplain(api_key="test")

        # Should not be the exact same class as base
        assert aixplain.Model != Model
        assert aixplain.Agent != Agent
        assert aixplain.Tool != Tool
        assert aixplain.Utility != Utility
        assert aixplain.Integration != Integration


class TestAixplainMultiInstance:
    """Tests for multi-instance support."""

    def test_multiple_instances_independent(self):
        """Multiple Aixplain instances should be independent."""
        aix_a = Aixplain(api_key="key_a")
        aix_b = Aixplain(api_key="key_b")

        assert aix_a.api_key != aix_b.api_key
        assert aix_a.client is not aix_b.client

    def test_multiple_instances_different_resources(self):
        """Resource classes should be different across instances."""
        aix_a = Aixplain(api_key="key_a")
        aix_b = Aixplain(api_key="key_b")

        assert aix_a.Model is not aix_b.Model
        assert aix_a.Agent is not aix_b.Agent
        assert aix_a.Tool is not aix_b.Tool

    def test_multiple_instances_different_contexts(self):
        """Resource contexts should point to correct instances."""
        aix_a = Aixplain(api_key="key_a")
        aix_b = Aixplain(api_key="key_b")

        assert aix_a.Model.context is aix_a
        assert aix_b.Model.context is aix_b
        assert aix_a.Model.context is not aix_b.Model.context

    def test_multiple_instances_same_key_still_independent(self):
        """Instances with same key should still be independent."""
        aix_1 = Aixplain(api_key="same_key")
        aix_2 = Aixplain(api_key="same_key")

        assert aix_1 is not aix_2
        assert aix_1.Model is not aix_2.Model
        assert aix_1.client is not aix_2.client


class TestAixplainEnumAccess:
    """Tests for enum access on Aixplain class."""

    def test_function_enum_has_expected_members(self):
        """Function enum should have expected members like 'text-generation'."""
        aixplain = Aixplain(api_key="test")

        # Function is an enum class with actual members
        from aixplain.v2 import enums

        assert aixplain.Function is enums.Function
        # Verify it has at least some expected members
        assert hasattr(aixplain.Function, "text_generation") or len(list(aixplain.Function)) > 0

    def test_supplier_enum_has_expected_members(self):
        """Supplier enum should have expected members."""
        aixplain = Aixplain(api_key="test")

        from aixplain.v2 import enums

        assert aixplain.Supplier is enums.Supplier
        # Verify it's an actual enum with members
        assert len(list(aixplain.Supplier)) > 0

    def test_language_enum_has_expected_members(self):
        """Language enum should have expected language members."""
        aixplain = Aixplain(api_key="test")

        from aixplain.v2 import enums

        assert aixplain.Language is enums.Language
        # Should have common languages
        assert len(list(aixplain.Language)) > 0

    def test_sort_by_enum_has_expected_values(self):
        """SortBy enum should have expected sorting options."""
        aixplain = Aixplain(api_key="test")

        from aixplain.v2 import enums

        assert aixplain.SortBy is enums.SortBy
        # SortBy should have common sort fields
        members = [m.name for m in aixplain.SortBy]
        assert len(members) > 0

    def test_sort_order_enum_has_asc_and_desc(self):
        """SortOrder enum should have 'asc' and 'desc' options."""
        aixplain = Aixplain(api_key="test")

        from aixplain.v2 import enums

        assert aixplain.SortOrder is enums.SortOrder
        # SortOrder should have asc/desc
        member_names = [m.name.lower() for m in aixplain.SortOrder]
        assert "asc" in member_names or "ascending" in member_names
        assert "desc" in member_names or "descending" in member_names

    def test_enums_are_class_attributes_not_instance(self):
        """Enums should be class attributes, same across instances."""
        aix_a = Aixplain(api_key="key_a")
        aix_b = Aixplain(api_key="key_b")

        # Enums should be the exact same objects (class-level)
        assert aix_a.Function is aix_b.Function
        assert aix_a.Supplier is aix_b.Supplier
        assert aix_a.Language is aix_b.Language
        assert aix_a.SortBy is aix_b.SortBy
        assert aix_a.SortOrder is aix_b.SortOrder
