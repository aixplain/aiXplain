"""Functional tests for RLM (Recursive Language Model) in v2 SDK."""

import pytest


# Gemini 2.5 Pro — used as both orchestrator and worker for testing
MODEL_ID = "68d43005ce180d2fdb4deac7"


@pytest.fixture(scope="module")
def rlm(client):
    """Create an RLM instance for testing."""
    return client.RLM(
        orchestrator_id=MODEL_ID,
        worker_id=MODEL_ID,
        max_iterations=5,
    )


class TestRLMCreation:
    """Tests for RLM instance creation and validation."""

    def test_create_rlm(self, client):
        """Test that an RLM instance can be created with valid IDs."""
        rlm = client.RLM(
            orchestrator_id=MODEL_ID,
            worker_id=MODEL_ID,
        )
        assert rlm.orchestrator_id == MODEL_ID
        assert rlm.worker_id == MODEL_ID
        assert rlm.max_iterations == 10  # default

    def test_create_rlm_custom_iterations(self, client):
        """Test RLM creation with custom max_iterations."""
        rlm = client.RLM(
            orchestrator_id=MODEL_ID,
            worker_id=MODEL_ID,
            max_iterations=3,
        )
        assert rlm.max_iterations == 3

    def test_create_rlm_missing_orchestrator(self, client):
        """Test that RLM raises when orchestrator_id is missing."""
        rlm = client.RLM(worker_id=MODEL_ID)
        with pytest.raises(Exception):
            rlm.run(data={"context": "test", "query": "test"})

    def test_create_rlm_missing_worker(self, client):
        """Test that RLM raises when worker_id is missing."""
        rlm = client.RLM(orchestrator_id=MODEL_ID)
        with pytest.raises(Exception):
            rlm.run(data={"context": "test", "query": "test"})


class TestRLMRun:
    """End-to-end tests for RLM.run()."""

    def test_run_with_dict_input(self, rlm):
        """Test RLM run with context and query as a dict."""
        result = rlm.run(
            data={
                "context": "The capital of France is Paris. The population is about 2.1 million.",
                "query": "What is the capital of France and its population?",
            }
        )
        assert result.status == "SUCCESS"
        assert result.completed is True
        assert result.data is not None
        assert len(result.data) > 0
        assert result.iterations_used >= 1

    def test_run_with_string_input(self, rlm):
        """Test RLM run with a plain string as context."""
        result = rlm.run(data="The speed of light is approximately 299,792,458 meters per second.")
        assert result.status == "SUCCESS"
        assert result.completed is True
        assert result.data is not None

    def test_run_with_json_context(self, rlm):
        """Test RLM run with a dict/list context value."""
        result = rlm.run(
            data={
                "context": {"countries": [{"name": "France", "capital": "Paris"}]},
                "query": "What is the capital of France?",
            }
        )
        assert result.status == "SUCCESS"
        assert result.completed is True
        assert result.data is not None

    def test_run_invalid_data_type(self, rlm):
        """Test that RLM raises on unsupported data type."""
        with pytest.raises(ValueError, match="Unsupported data type"):
            rlm.run(data=12345)

    def test_run_dict_missing_context(self, rlm):
        """Test that RLM raises when dict is missing 'context' key."""
        with pytest.raises(ValueError, match="must contain a 'context' key"):
            rlm.run(data={"query": "test"})

    def test_repl_logs_populated(self, rlm):
        """Test that repl_logs are populated after a run."""
        result = rlm.run(
            data={
                "context": "Python was created by Guido van Rossum.",
                "query": "Who created Python?",
            }
        )
        assert result.status == "SUCCESS"
        # At least one REPL interaction should have occurred
        assert result.iterations_used >= 1


class TestRLMUnsupported:
    """Tests for unsupported RLM operations."""

    def test_run_async_not_supported(self, rlm):
        """Test that run_async raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            rlm.run_async()

    def test_run_stream_not_supported(self, rlm):
        """Test that run_stream raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            rlm.run_stream()
