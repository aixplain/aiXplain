import os
from aixplain.v2.core import Aixplain
from aixplain.v2.model import Model
from aixplain.v2.tool import Tool
from aixplain.v2.agent import Agent
from unittest.mock import patch


def test_aixplain_instance():
    # mock init_client, init_resources
    with patch.object(Aixplain, "init_client"):
        with patch.object(Aixplain, "init_resources"):
            aixplain = Aixplain(api_key="test")
            assert aixplain is not None
            assert aixplain.api_key == "test"
            assert (
                aixplain.backend_url == os.getenv("BACKEND_URL")
                or "https://platform-api.aixplain.com"
            )
            assert aixplain.pipeline_url == os.getenv("PIPELINES_RUN_URL") or (
                "https://platform-api.aixplain.com/assets/pipeline/" "execution/run"
            )
            assert (
                aixplain.model_url == os.getenv("MODELS_RUN_URL")
                or "https://models.aixplain.com/api/v2/execute"
            )
            aixplain.init_client.assert_called_once()
            aixplain.init_resources.assert_called_once()


def test_aixplain_environment_variables():
    """Test that environment variables are used when no explicit values provided."""
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


def test_aixplain_init_client():
    aixplain = Aixplain(api_key="test")
    with patch("aixplain.v2.core.AixplainClient") as mock_client:
        aixplain.init_client()
        mock_client.assert_called_once_with(
            base_url=aixplain.backend_url,
            team_api_key="test",
        )
        assert aixplain.client is not None


def test_aixplain_init_resources():
    aixplain = Aixplain(api_key="test")
    with patch.object(Aixplain, "init_resources"):
        aixplain.init_resources()
        assert aixplain.Model is not None
        assert aixplain.Tool is not None
        assert aixplain.Agent is not None
        assert aixplain.Model.context == aixplain
        assert aixplain.Tool.context == aixplain
        assert aixplain.Agent.context == aixplain

        assert issubclass(aixplain.Model, Model)
        assert issubclass(aixplain.Tool, Tool)
        assert issubclass(aixplain.Agent, Agent)

        # check if the resources are NOT the same class type
        assert aixplain.Tool != Tool
        assert aixplain.Model != Model
        assert aixplain.Agent != Agent
