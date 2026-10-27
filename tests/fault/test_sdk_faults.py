"""SDK calls against faults on real sockets (ENG-3782, layer 3).

ENG-3761 listed 7 SDK fixes in this class: #1014 (no default timeout),
BUG-1090/#1045 (a POST re-sent after a read timeout, billing twice),
BUG-1097 (a poll read longer than the run's budget), BUG-942 (no jitter, no
Retry-After), #1041. Their tests patch ``session.request``; these put a real
server behind a proxy that stalls, drops or slows the connection.
"""

import time

import pytest

from tests.fault.conftest import READ_TIMEOUT_S, Faulty
from tests.fault.servers import FaultResponse
from tests.support.platform_replay import RecordedRequest, StubResponse, load_recording

LLM_ID = "6646261c6eb563165658bbb1"
GRACE_S = 3.0


def _llm(faulty: Faulty) -> None:
    faulty.stub.serve("backend/model-detail-llm")


def test_baseline_run_through_the_proxy(faulty: Faulty) -> None:
    _llm(faulty)
    faulty.stub.serve("models/llm-run-success")

    result = faulty.client.Model.get(LLM_ID).run(text="hi")

    assert result.data == "Paris is the capital of France."


def test_run_that_stalls_after_headers_fails_at_the_read_timeout_without_resubmitting(faulty: Faulty) -> None:
    # #1014: a default read timeout on every request; BUG-1090: a POST whose
    # bytes reached the server is never sent again.
    _llm(faulty)
    model = faulty.client.Model.get(LLM_ID)
    faulty.stub.route(
        "POST", "models", "/" + LLM_ID, FaultResponse(body={"status": "SUCCESS"}, stall_after_headers_s=60)
    )

    started = time.monotonic()
    with pytest.raises(Exception):  # noqa: B017  (requests' ReadTimeout/ConnectionError, however the SDK wraps it)
        model.run(text="hi")

    assert time.monotonic() - started < READ_TIMEOUT_S + GRACE_S
    assert len(faulty.stub.sent("POST", LLM_ID)) == 1


def test_run_closed_without_a_response_is_not_resubmitted(faulty: Faulty) -> None:
    # BUG-1090: the SDK cannot know whether the platform ran it, so it must not run it twice.
    _llm(faulty)
    model = faulty.client.Model.get(LLM_ID)
    faulty.stub.route("POST", "models", "/" + LLM_ID, FaultResponse(close_without_response=True))

    with pytest.raises(Exception):  # noqa: B017
        model.run(text="hi")

    assert len(faulty.stub.sent("POST", LLM_ID)) == 1


def test_503_burst_on_a_read_is_retried(faulty: Faulty) -> None:
    unavailable = StubResponse(status=503, body={"statusCode": 503, "message": "Service Unavailable"})
    served = []

    def detail(_request: RecordedRequest, _params: dict) -> StubResponse:
        served.append(1)
        if len(served) <= 3:
            return unavailable
        return StubResponse(body=load_recording("backend/model-detail-llm")["response"]["json"])

    faulty.stub.route("GET", "backend", "/v2/models/{id}", detail)

    started = time.monotonic()
    model = faulty.client.Model.get(LLM_ID)

    assert model.id == LLM_ID and len(served) == 4
    assert time.monotonic() - started < 15


def test_retry_after_on_a_rate_limited_read_is_honoured(faulty: Faulty) -> None:
    # BUG-942: 429 is retried and its Retry-After is waited out.
    calls = []

    def detail(_request: RecordedRequest, _params: dict) -> StubResponse:
        calls.append(time.monotonic())
        if len(calls) == 1:
            return StubResponse(
                status=429,
                body={"statusCode": 429, "message": "Too Many Requests"},
                headers={"Content-Type": "application/json", "Retry-After": "2"},
            )
        return StubResponse(body=load_recording("backend/model-detail-llm")["response"]["json"])

    faulty.stub.route("GET", "backend", "/v2/models/{id}", detail)

    faulty.client.Model.get(LLM_ID)

    assert len(calls) == 2 and calls[1] - calls[0] >= 1.9


def test_poll_that_stops_answering_ends_within_the_run_budget(faulty: Faulty) -> None:
    # BUG-1097: each poll read is bounded by the time the run has left, not by
    # the 300 s default read timeout.
    _llm(faulty)
    model = faulty.client.Model.get(LLM_ID)
    faulty.stub.serve("models/run-in-progress")
    faulty.stub.serve("models/poll-in-progress")
    calls = []
    faulty.stub.route(
        "GET",
        "models_root",
        "/api/v1/data/{request_id}",
        lambda r, p: (calls.append(1), FaultResponse(body={}, stall_after_headers_s=60))[1],
    )

    started = time.monotonic()
    with pytest.raises(Exception):  # noqa: B017
        model.run(text="hi", timeout=5)

    assert time.monotonic() - started < 5 + READ_TIMEOUT_S + GRACE_S
    assert len(faulty.stub.sent("POST", LLM_ID)) == 1


def test_slow_body_is_waited_for(faulty: Faulty) -> None:
    _llm(faulty)
    model = faulty.client.Model.get(LLM_ID)
    faulty.stub.serve("models/llm-run-success")
    faulty.toxic("models", "bandwidth", rate=1)

    started = time.monotonic()
    result = model.run(text="hi")

    assert result.data == "Paris is the capital of France."
    assert time.monotonic() - started > 1.0
