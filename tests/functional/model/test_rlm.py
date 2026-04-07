"""Functional tests for RLM (Recursive Language Model) in v1 SDK."""

import pytest
from aixplain.factories import ModelFactory
from aixplain.modules.model.rlm import RLM


# Gemini 2.5 Pro — used as both orchestrator and worker for testing
MODEL_ID = "68d43005ce180d2fdb4deac7"


@pytest.fixture(scope="module")
def rlm():
    """Create an RLM instance via ModelFactory."""
    return ModelFactory.create_rlm(
        orchestrator_model_id=MODEL_ID,
        worker_model_id=MODEL_ID,
        max_iterations=5,
    )


class TestRLMCreation:
    """Tests for RLM instance creation."""

    def test_create_rlm(self):
        """Test that create_rlm returns a valid RLM instance."""
        rlm = ModelFactory.create_rlm(
            orchestrator_model_id=MODEL_ID,
            worker_model_id=MODEL_ID,
        )
        assert isinstance(rlm, RLM)
        assert rlm.orchestrator is not None
        assert rlm.worker is not None
        assert rlm.max_iterations == 10  # default

    def test_create_rlm_custom_iterations(self):
        """Test RLM creation with custom max_iterations."""
        rlm = ModelFactory.create_rlm(
            orchestrator_model_id=MODEL_ID,
            worker_model_id=MODEL_ID,
            max_iterations=3,
        )
        assert rlm.max_iterations == 3


class TestRLMRun:
    """End-to-end tests for RLM.run()."""

    def test_run_with_dict_input(self, rlm):
        """Test RLM run with context and query as a dict."""
        response = rlm.run(
            data={
                "context": "The capital of France is Paris. The population is about 2.1 million.",
                "query": "What is the capital of France and its population?",
            }
        )
        assert response["completed"] is True
        assert response["status"].value == "SUCCESS" or str(response["status"]) == "SUCCESS"
        assert response["data"] is not None
        assert len(response["data"]) > 0
        assert response["iterations_used"] >= 1

    def test_run_with_string_input(self, rlm):
        """Test RLM run with a plain string as context."""
        response = rlm.run(data="The speed of light is approximately 299,792,458 meters per second.")
        assert response["completed"] is True
        assert response["data"] is not None

    def test_run_with_json_context(self, rlm):
        """Test RLM run with a dict/list context value."""
        response = rlm.run(
            data={
                "context": {"countries": [{"name": "France", "capital": "Paris"}]},
                "query": "What is the capital of France?",
            }
        )
        assert response["completed"] is True
        assert response["data"] is not None

    def test_run_invalid_data_type(self, rlm):
        """Test that RLM raises on unsupported data type."""
        with pytest.raises(ValueError, match="Unsupported data type"):
            rlm.run(data=12345)

    def test_run_dict_missing_context(self, rlm):
        """Test that RLM raises when dict is missing 'context' key."""
        with pytest.raises(ValueError, match="must contain a 'context' key"):
            rlm.run(data={"query": "test"})


class TestRLMUnsupported:
    """Tests for unsupported RLM operations."""

    def test_run_async_not_supported(self, rlm):
        """Test that run_async raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            rlm.run_async(data="test")

    def test_run_stream_not_supported(self, rlm):
        """Test that run_stream raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            rlm.run_stream(data="test")
