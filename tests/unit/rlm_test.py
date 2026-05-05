"""Unit tests for RLM context resolution, sandbox setup, credit tracking, and context window."""

import json
from unittest.mock import MagicMock, patch

import pytest

from aixplain.v1.modules.model.rlm import RLM as RLMV1
from aixplain.v2.rlm import RLM as RLMV2, RLMResult


# Parametrize over both implementations
RLM_IMPLS = [
    pytest.param(RLMV1, id="v1"),
    pytest.param(RLMV2, id="v2"),
]


# _resolve_context
class TestResolveContext:
    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_local_text_file(self, RLM, tmp_path):
        p = tmp_path / "doc.txt"
        p.write_text("file content", encoding="utf-8")
        assert RLM._resolve_context(str(p)) == "file content"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_local_json_file(self, RLM, tmp_path):
        data = {"a": 1}
        p = tmp_path / "data.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        assert RLM._resolve_context(str(p)) == data

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_pathlib_path(self, RLM, tmp_path):
        p = tmp_path / "doc.txt"
        p.write_text("pathlib content", encoding="utf-8")
        assert RLM._resolve_context(p) == "pathlib content"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_raw_string(self, RLM):
        assert RLM._resolve_context("just raw text") == "just raw text"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_dict_passthrough(self, RLM):
        d = {"x": 1}
        assert RLM._resolve_context(d) is d

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_list_passthrough(self, RLM):
        lst = [1, 2, 3]
        assert RLM._resolve_context(lst) is lst

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_non_string_fallback(self, RLM):
        assert RLM._resolve_context(42) == "42"

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_http_url_passes_through_unchanged(self, RLM):
        url = "http://example.com/doc.txt"
        assert RLM._resolve_context(url) == url

    @pytest.mark.parametrize("RLM", RLM_IMPLS)
    def test_https_url_passes_through_unchanged(self, RLM):
        url = "https://example.com/data.json"
        assert RLM._resolve_context(url) == url


# _setup_repl — URL branch
def _make_v1_rlm() -> RLMV1:
    """Minimal v1 RLM with stubbed models."""
    rlm = RLMV1.__new__(RLMV1)
    rlm.api_key = "test-key"
    rlm.orchestrator = MagicMock()
    rlm.worker = MagicMock()
    rlm.worker.url = "https://models.aixplain.com/api/v2/execute"
    rlm.worker.id = "worker-id"
    rlm.worker.additional_info = {}
    rlm._session_id = None
    rlm._sandbox_tool = None
    rlm._messages = []
    rlm._used_credits = 0.0
    return rlm


def _make_v2_rlm() -> RLMV2:
    """Minimal v2 RLM with stubbed context client."""
    rlm = RLMV2.__new__(RLMV2)
    rlm.orchestrator_id = "orch-id"
    rlm.worker_id = "worker-id"
    rlm.max_iterations = 10
    rlm.timeout = 600.0
    rlm._session_id = None
    rlm._sandbox_tool = None
    rlm._orchestrator = None
    rlm._worker = None
    rlm._messages = []
    rlm._used_credits = 0.0
    client = MagicMock()
    client.backend_url = "https://platform-api.aixplain.com"
    client.api_key = "test-key"
    client.model_url = "https://models.aixplain.com/api/v2/execute"
    rlm.context = client
    return rlm


class TestSetupReplURLPath:
    def test_v1_url_skips_file_factory(self):
        rlm = _make_v1_rlm()
        sandbox_mock = MagicMock()

        with (
            patch("aixplain.factories.tool_factory.ToolFactory") as mock_tf,
            patch("aixplain.factories.file_factory.FileFactory") as mock_ff,
        ):
            mock_tf.get.return_value = sandbox_mock
            rlm._setup_repl("https://example.com/doc.txt")

        mock_ff.create.assert_not_called()

    def test_v1_url_sandbox_code_contains_url(self):
        rlm = _make_v1_rlm()
        sandbox_mock = MagicMock()
        captured = []

        def capture_run(inputs, action):
            captured.append(inputs["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run

        with patch("aixplain.factories.tool_factory.ToolFactory") as mock_tf:
            mock_tf.get.return_value = sandbox_mock
            rlm._setup_repl("https://example.com/doc.txt")

        context_code = captured[0]
        assert "https://example.com/doc.txt" in context_code
        assert "_content_type" in context_code
        assert "_is_json" in context_code
        assert "__json.load" in context_code

    def test_v2_url_skips_file_uploader(self):
        rlm = _make_v2_rlm()
        sandbox_mock = MagicMock()
        rlm._sandbox_tool = sandbox_mock

        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            rlm._setup_repl("https://example.com/doc.txt")

        mock_uploader.assert_not_called()

    def test_v2_url_sandbox_code_contains_url(self):
        rlm = _make_v2_rlm()
        sandbox_mock = MagicMock()
        rlm._sandbox_tool = sandbox_mock
        captured = []

        def capture_run(data, action):
            captured.append(data["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run

        rlm._setup_repl("https://example.com/doc.txt")

        context_code = captured[0]
        assert "https://example.com/doc.txt" in context_code
        assert "_content_type" in context_code
        assert "_is_json" in context_code
        assert "__json.load" in context_code


# Credit tracking
def _sandbox_result(stdout="", stderr="", used_credits=0.0):
    """Create a mock sandbox result."""
    r = MagicMock()
    r.data = {"stdout": stdout, "stderr": stderr}
    r.used_credits = used_credits
    return r


def _model_response_v1(data="response text", used_credits=0.0, completed=True, status="SUCCESS"):
    """Create a mock v1 model response."""
    r = MagicMock()
    r.data = data
    r.used_credits = used_credits
    r.get = lambda k, default=None: {"completed": completed, "data": data, "status": status, "error_message": ""}.get(
        k, default
    )
    r.__getitem__ = lambda self_, k: {"completed": completed, "data": data, "status": status}.get(k)
    return r


class TestV1CreditTracking:
    def test_orchestrator_credits_accumulated(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm.orchestrator.run.return_value = _model_response_v1(used_credits=0.05)

        rlm._orchestrator_completion([{"role": "user", "content": "test"}])

        assert rlm._used_credits == pytest.approx(0.05)

    def test_sandbox_credits_accumulated(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm._sandbox_tool = MagicMock()
        rlm._sandbox_tool.run.return_value = _sandbox_result(used_credits=0.01)
        rlm._session_id = "test-session"

        rlm._run_sandbox("print('hello')")

        assert rlm._used_credits == pytest.approx(0.01)

    def test_execute_code_credits_accumulated(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm._sandbox_tool = MagicMock()
        rlm._sandbox_tool.run.return_value = _sandbox_result(stdout="done", used_credits=0.02)
        rlm._session_id = "test-session"

        output = rlm._execute_code("x = 1\nprint('done')")

        assert "done" in output
        assert rlm._used_credits == pytest.approx(0.02)

    def test_collect_llm_query_credits(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 1.0
        rlm._sandbox_tool = MagicMock()
        rlm._session_id = "test-session"
        rlm._sandbox_tool.run.return_value = _sandbox_result(stdout="0.35", used_credits=0.0)

        rlm._collect_llm_query_credits()

        assert rlm._used_credits == pytest.approx(1.35)

    def test_multiple_calls_accumulate(self):
        rlm = _make_v1_rlm()
        rlm._used_credits = 0.0
        rlm._session_id = "test-session"
        rlm._sandbox_tool = MagicMock()

        rlm.orchestrator.run.return_value = _model_response_v1(used_credits=0.1)
        rlm._orchestrator_completion([{"role": "user", "content": "a"}])
        rlm._orchestrator_completion([{"role": "user", "content": "b"}])

        rlm._sandbox_tool.run.return_value = _sandbox_result(stdout="ok", used_credits=0.05)
        rlm._execute_code("pass")
        rlm._execute_code("pass")

        assert rlm._used_credits == pytest.approx(0.3)


class TestV2CreditTracking:
    def test_orchestrator_credits_accumulated(self):
        rlm = _make_v2_rlm()
        rlm._used_credits = 0.0
        mock_model = MagicMock()
        resp = MagicMock()
        resp.completed = True
        resp.status = "SUCCESS"
        resp.data = "answer"
        resp.used_credits = 0.07
        mock_model.run.return_value = resp
        rlm._orchestrator = mock_model

        rlm._orchestrator_completion([{"role": "user", "content": "test"}])

        assert rlm._used_credits == pytest.approx(0.07)

    def test_sandbox_credits_accumulated(self):
        rlm = _make_v2_rlm()
        rlm._used_credits = 0.0
        sandbox = MagicMock()
        sandbox.run.return_value = _sandbox_result(used_credits=0.03)
        rlm._session_id = "test-session"

        rlm._run_sandbox(sandbox, "print('hi')")

        assert rlm._used_credits == pytest.approx(0.03)

    def test_execute_code_credits_accumulated(self):
        rlm = _make_v2_rlm()
        rlm._used_credits = 0.0
        sandbox = MagicMock()
        sandbox.run.return_value = _sandbox_result(stdout="done", used_credits=0.04)
        rlm._sandbox_tool = sandbox
        rlm._session_id = "test-session"

        output = rlm._execute_code("print('done')")

        assert "done" in output
        assert rlm._used_credits == pytest.approx(0.04)

    def test_collect_llm_query_credits(self):
        rlm = _make_v2_rlm()
        rlm._used_credits = 2.0
        sandbox = MagicMock()
        sandbox.run.return_value = _sandbox_result(stdout="0.50", used_credits=0.0)
        rlm._sandbox_tool = sandbox
        rlm._session_id = "test-session"

        rlm._collect_llm_query_credits()

        assert rlm._used_credits == pytest.approx(2.50)

    def test_used_credits_field_on_rlm_result(self):
        result = RLMResult(status="SUCCESS", completed=True, data="answer")
        result.used_credits = 1.23
        result.iterations_used = 5

        assert result.used_credits == pytest.approx(1.23)
        serialized = result.to_dict()
        assert serialized["usedCredits"] == pytest.approx(1.23)


class TestLlmQueryCodeCreditsTracking:
    def test_v1_llm_query_code_accumulates_credits(self):
        rlm = _make_v1_rlm()
        sandbox_mock = MagicMock()
        captured = []

        def capture_run(inputs, action):
            captured.append(inputs["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run

        with (
            patch("aixplain.factories.tool_factory.ToolFactory") as mock_tf,
            patch("aixplain.factories.file_factory.FileFactory") as mock_ff,
        ):
            mock_tf.get.return_value = sandbox_mock
            mock_ff.create.return_value = "https://storage.example.com/ctx.txt"
            rlm._setup_repl("raw text context")

        llm_query_code = captured[-1]
        assert "_total_llm_query_credits" in llm_query_code
        assert "global _total_llm_query_credits" in llm_query_code
        assert "usedCredits" in llm_query_code

    def test_v2_llm_query_code_accumulates_credits(self):
        rlm = _make_v2_rlm()
        sandbox_mock = MagicMock()
        captured = []

        def capture_run(data, action):
            captured.append(data["code"])
            return MagicMock(used_credits=0)

        sandbox_mock.run.side_effect = capture_run
        rlm._sandbox_tool = sandbox_mock

        with patch("aixplain.v2.rlm.FileUploader") as mock_uploader:
            uploader_instance = MagicMock()
            uploader_instance.upload.return_value = "https://storage.example.com/ctx.txt"
            mock_uploader.return_value = uploader_instance
            rlm._setup_repl("raw text context")

        llm_query_code = captured[-1]
        assert "_total_llm_query_credits" in llm_query_code
        assert "global _total_llm_query_credits" in llm_query_code
        assert "usedCredits" in llm_query_code


# Worker context window
class TestV1WorkerContextWindow:
    def test_returns_formatted_k_tokens(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "128000"}]}
        assert rlm._get_worker_context_window() == "128K tokens"

    def test_returns_formatted_m_tokens(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "1048576"}]}
        assert rlm._get_worker_context_window() == "1.0M tokens"

    def test_returns_small_token_count(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "512"}]}
        assert rlm._get_worker_context_window() == "512 tokens"

    def test_fallback_when_no_attributes(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {}
        assert rlm._get_worker_context_window() == "a large context window"

    def test_fallback_when_attribute_missing(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "other_attr", "code": "100"}]}
        assert rlm._get_worker_context_window() == "a large context window"

    def test_non_numeric_returns_raw_string(self):
        rlm = _make_v1_rlm()
        rlm.worker.additional_info = {"attributes": [{"name": "max_context_length", "code": "unlimited"}]}
        assert rlm._get_worker_context_window() == "unlimited"


class TestV2WorkerContextWindow:
    def test_returns_formatted_k_tokens(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": "200000"}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "200K tokens"

    def test_returns_formatted_m_tokens(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": "2000000"}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "2.0M tokens"

    def test_fallback_when_no_attributes(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "a large context window"

    def test_fallback_when_attributes_none(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = None
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "a large context window"

    def test_non_numeric_returns_raw_string(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": "very_large"}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "very_large"

    def test_integer_attribute_value(self):
        rlm = _make_v2_rlm()
        mock_worker = MagicMock()
        mock_worker.attributes = {"max_context_length": 32000}
        rlm._worker = mock_worker
        assert rlm._get_worker_context_window() == "32K tokens"
