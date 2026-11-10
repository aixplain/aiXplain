"""Recorded model streams replayed through the SDK's streamer (ENG-3782, layer 2).

Each file in ``streams/`` is an SSE body ``/api/v2/execute`` returns, with what
the SDK's ``ModelResponseStreamer`` should yield for it: the assembled
content and reasoning, the tool calls, the last finish_reason and usage, and
the stream's final status. The body is served on the wire to the real
``Model.run_stream``. SDK #987, #1012 and BUG-1094 were each tested with chunk
objects built by hand. The SSE bodies are shared with aixplain-agents'
tests/stream_replay; a file whose expected result the SDK does not produce yet
carries ``known_failure`` and runs as a strict xfail.
"""

import json
from pathlib import Path

import pytest

from aixplain.v2.exceptions import APIError
from tests.support.platform_replay import PlatformStub, StubResponse, fill

STREAMS = Path(__file__).parent / "streams"
LLM_ID = "6646261c6eb563165658bbb1"


def _cases() -> list:
    cases = []
    for path in sorted(STREAMS.rglob("*.json")):
        name = path.relative_to(STREAMS).with_suffix("").as_posix()
        spec = json.loads(path.read_text(encoding="utf-8"))
        marks = [pytest.mark.xfail(strict=True, reason=spec["known_failure"])] if spec.get("known_failure") else []
        cases.append(pytest.param(spec, id=name, marks=marks))
    return cases


@pytest.mark.parametrize("spec", _cases())
def test_stream_yields_its_recorded_meaning(aix, platform: PlatformStub, spec: dict) -> None:
    response = spec["response"]
    platform.serve("backend/model-detail-llm")
    platform.route(
        "POST",
        "models",
        "/" + LLM_ID,
        StubResponse(
            status=response["status"],
            headers=response["headers"],
            sse=response.get("sse"),
            body=fill(response.get("json")),
        ),
    )
    expected = spec["expected"]
    model = aix.Model.get(LLM_ID)

    if "raises_with" in expected:
        with pytest.raises(APIError) as raised:
            list(model.run_stream(text="replay"))
        assert expected["raises_with"] in str(raised.value)
        return

    streamer = model.run_stream(text="replay")
    content, reasoning, names, finish, usage, errors = "", "", [], None, None, []
    for chunk in streamer:
        content += chunk.data or ""
        reasoning += chunk.reasoning_content or ""
        for call in chunk.tool_calls or []:
            name = (call.get("function") or {}).get("name")
            if name:
                names.append(name)
        finish = chunk.finish_reason or finish
        usage = chunk.usage or usage
        if chunk.error_message:
            errors.append(chunk.error_message)

    assert str(getattr(streamer.status, "value", streamer.status)) == expected["status"]
    if "error_message_contains" in expected:
        assert any(expected["error_message_contains"] in e for e in errors), errors
        return
    if "content_must_not_contain" in expected:
        assert expected["content_must_not_contain"] not in content
        return
    assert content == expected["content"]
    assert reasoning == expected["reasoning"]
    assert finish == expected["finish_reason"]
    if "tool_call_names" in expected:
        assert names == expected["tool_call_names"]
    if "usage" in expected:
        assert (usage["prompt_tokens"], usage["completion_tokens"]) == (
            expected["usage"]["prompt_tokens"],
            expected["usage"]["completion_tokens"],
        )
