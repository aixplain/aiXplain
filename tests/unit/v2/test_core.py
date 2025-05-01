import os
from aixplain.v2.core import Aixplain
from aixplain.v2.model import Model
from aixplain.v2.pipeline import Pipeline
from aixplain.v2.agent import Agent
from unittest.mock import patch


def test_aixplain_instance():
    # mock init_env, init_client, init_resources
    with patch.object(Aixplain, "init_env"):
        with patch.object(Aixplain, "init_client"):
            with patch.object(Aixplain, "init_resources"):
                aixplain = Aixplain(api_key="test")
                assert aixplain is not None
                assert aixplain.api_key == "test"
                assert aixplain.base_url == os.getenv("BACKEND_URL") or "https://platform-api.aixplain.com"
                assert (
                    aixplain.pipeline_url == os.getenv("PIPELINES_RUN_URL")
                    or "https://platform-api.aixplain.com/assets/pipeline/execution/run"
                )
                assert aixplain.model_url == os.getenv("MODELS_RUN_URL") or "https://models.aixplain.com/api/v1/execute"
                aixplain.init_env.assert_called_once()
                aixplain.init_client.assert_called_once()
                aixplain.init_resources.assert_called_once()


def test_aixplain_init_env():
    aixplain = Aixplain(
        api_key="test",
        backend_url="https://platform-api.aixplain.com",
        pipeline_url="https://platform-api.aixplain.com/assets/pipeline/execution/run",
        model_url="https://models.aixplain.com/api/v1/execute",
    )
    with patch.object(os, "environ", new=dict()) as mock_environ:
        aixplain.init_env()
        assert mock_environ["TEAM_API_KEY"] == "test"
        assert mock_environ["BACKEND_URL"] == "https://platform-api.aixplain.com"
        assert mock_environ["PIPELINE_URL"] == "https://platform-api.aixplain.com/assets/pipeline/execution/run"
        assert mock_environ["MODEL_URL"] == "https://models.aixplain.com/api/v1/execute"


def test_aixplain_init_client():
    aixplain = Aixplain(api_key="test")
    with patch("aixplain.v2.core.AixplainClient") as mock_client:
        aixplain.init_client()
        mock_client.assert_called_once_with(
            base_url="https://platform-api.aixplain.com",
            team_api_key="test",
        )
        assert aixplain.client is not None


def test_aixplain_init_resources():
    aixplain = Aixplain(api_key="test")
    with patch.object(Aixplain, "init_resources"):
        aixplain.init_resources()
        assert aixplain.Model is not None
        assert aixplain.Pipeline is not None
        assert aixplain.Agent is not None
        assert aixplain.Model.context == aixplain
        assert aixplain.Pipeline.context == aixplain
        assert aixplain.Agent.context == aixplain

        assert issubclass(aixplain.Model, Model)
        assert issubclass(aixplain.Pipeline, Pipeline)
        assert issubclass(aixplain.Agent, Agent)

        # check if the resources are NOT the same class type
        assert aixplain.Pipeline != Pipeline
        assert aixplain.Model != Model
        assert aixplain.Agent != Agent
