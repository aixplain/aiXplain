"""Models, tools and files against platform-shaped responses (ENG-3782, layer 1).

Model and tool detail follow platform-backend's transformModelForSDKV2; run
envelopes follow the models service as the SDK and the agents provider parse
it. Error bodies are NestJS's, plus the models service's supplierError.
"""

import pytest

from aixplain.v2.exceptions import APIError
from tests.support.platform_replay import MODELS_ROOT_URL, PlatformStub, StubResponse, load_recording

LLM_ID = "6646261c6eb563165658bbb1"
TOOL_ID = "66f423426eb563fa213a3531"


def test_model_detail_hydrates(aix, platform: PlatformStub) -> None:
    platform.serve("backend/model-detail-llm")

    model = aix.Model.get(LLM_ID)

    assert (model.id, model.name) == (LLM_ID, "GPT-4o Mini")
    assert model.supports_streaming is True
    assert model.connection_type == ["synchronous"]
    assert {p.name for p in model.params} >= {"text", "max_tokens", "tools"}


def test_sync_llm_run_returns_answer_usage_and_credits(aix, platform: PlatformStub) -> None:
    platform.serve("backend/model-detail-llm").serve("models/llm-run-success")

    result = aix.Model.get(LLM_ID).run(text="Capital of France?")

    assert result.status == "SUCCESS"
    assert result.data == "Paris is the capital of France."
    assert (result.usage.prompt_tokens, result.usage.completion_tokens) == (42, 9)
    assert result.used_credits == pytest.approx(0.0000117)


def test_native_tool_call_survives_into_the_result(aix, platform: PlatformStub) -> None:
    platform.serve("backend/model-detail-llm").serve("models/llm-run-tool-call")

    result = aix.Model.get(LLM_ID).run(text="Weather in Paris?")

    [detail] = result.details
    [call] = detail.message.tool_calls
    assert call["function"]["name"] == "get_weather"
    assert detail.finish_reason == "tool_calls"


def test_nan_token_counts_are_tolerated(aix, platform: PlatformStub) -> None:
    platform.serve("backend/model-detail-llm").serve("models/llm-run-nan-usage")

    result = aix.Model.get(LLM_ID).run(text="ok?")

    assert result.data == "ok"
    assert result.usage.prompt_tokens is None


def test_in_progress_run_is_polled_on_the_models_host(aix, platform: PlatformStub) -> None:
    platform.serve("backend/model-detail-llm").serve("models/run-in-progress")
    platform.serve("models/poll-in-progress", then=["models/poll-success"])

    result = aix.Model.get(LLM_ID).run(text="Translate: hello")

    assert result.data == "Translated text."
    polls = platform.sent("GET", "/api/v1/data/")
    assert len(polls) == 2 and all(p.url.startswith(MODELS_ROOT_URL) for p in polls)
    assert len(platform.sent("POST", LLM_ID)) == 1


def test_failed_run_raises_once_with_the_supplier_message(aix, platform: PlatformStub) -> None:
    platform.serve("backend/model-detail-llm").serve("models/llm-run-failed")

    with pytest.raises(APIError) as raised:
        aix.Model.get(LLM_ID).run(text="hi")

    assert "does not exist or you do not have access" in str(raised.value)
    assert raised.value.retryable is False
    assert len(platform.sent("POST", LLM_ID)) == 1  # BUG-1090: a FAILED body is never resubmitted


def test_supplier_error_detail_wins_on_a_non_2xx(aix, platform: PlatformStub) -> None:
    # #1032 / 854f723e: the specific supplierError, not the generic err.supplier_error code.
    platform.serve("backend/model-detail-llm").serve("models/error-supplier-400")

    with pytest.raises(APIError) as raised:
        aix.Model.get(LLM_ID).run(text="hi")

    assert "Name already exists" in str(raised.value)


@pytest.mark.parametrize(
    ("recording", "status", "message"),
    [
        ("models/error-not-enough-balance", 471, "err.not_enough_balance"),
        ("models/error-rate-limited", 429, "err.workspace.rpm_exceeded"),
    ],
)
def test_refused_run_is_not_resubmitted(aix, platform: PlatformStub, recording: str, status: int, message: str) -> None:
    platform.serve("backend/model-detail-llm").serve(recording)

    with pytest.raises(APIError) as raised:
        aix.Model.get(LLM_ID).run(text="hi")

    assert raised.value.status_code == status and message in str(raised.value)
    # BUG-1090: POST /execute is never retried after the request reached the server.
    assert len(platform.sent("POST", LLM_ID)) == 1


@pytest.mark.parametrize(("recording", "status"), [("backend/error-not-found", 404), ("backend/error-forbidden", 403)])
def test_get_error_envelope_becomes_an_api_error(aix, platform: PlatformStub, recording: str, status: int) -> None:
    platform.serve(recording)

    with pytest.raises(APIError) as raised:
        aix.Model.get(LLM_ID)

    assert raised.value.status_code == status
    assert load_recording(recording)["response"]["json"]["message"] in str(raised.value)


def test_tool_detail_with_an_empty_vendor_hydrates(aix, platform: PlatformStub) -> None:
    # GET /v2/tools/:id never sets teamData, so vendor and supplier are always {}.
    platform.serve("backend/tool-detail-utility")

    tool = aix.Tool.get(TOOL_ID)

    assert (tool.id, tool.name) == (TOOL_ID, "Google Search")


def test_tool_batch_get_returns_the_tools(aix, platform: PlatformStub) -> None:
    platform.serve("backend/tools-batch")

    batch = aix.Tool.get_many([TOOL_ID])

    assert list(batch.tools) == [TOOL_ID] and batch.tools[TOOL_ID].name == "Google Search"
    assert batch.missing == []
    [request] = platform.sent("GET", "/v2/tools")
    assert request.query == {"ids": [TOOL_ID]}


def test_file_asset_hydrates(aix, platform: PlatformStub) -> None:
    platform.route("GET", "backend", "/sdk/file-asset/{id}/children/recursive", StubResponse(body=[]))
    platform.serve("backend/file-asset-detail")

    file = aix.File.get("file-contract-1")

    assert (file.id, file.name) == ("file-contract-1", "guide.pdf")
