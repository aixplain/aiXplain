"""A canary API key, followed through the SDK's requests, logs and errors (ENG-3782, layer 5).

SDK #1040 (SEV1) sent the key to whatever host a poll URL or a redirect named;
SDK #1042 (SEV1) baked it into sandbox source (see test_rlm_sandbox_secrets.py).
Each was found by reading code. Here a unique key drives real SDK calls
against the recorded platform and every request, log record and error is
searched for it.
"""

import logging
import os

import pytest

from aixplain.v2.client import UntrustedURLError
from aixplain.v2.exceptions import APIError
from tests.support.platform_replay import BACKEND_URL, MODELS_ROOT_URL, PlatformStub, StubResponse, load_recording

LLM_ID = "6646261c6eb563165658bbb1"
AGENT_ID = "agent-contract-1"
FOREIGN = "https://collector.evil.test"


@pytest.fixture
def canary(api_key: str) -> str:
    return api_key


def _every_flow(aix, platform: PlatformStub) -> None:
    """Agent run and poll, model detail, run and stream, search, tool and file reads, and a failure."""
    platform.serve("backend/agent-detail").serve("backend/agent-run-submit")
    platform.serve("backend/agent-poll-in-progress", then=["backend/agent-poll-success"])
    platform.serve("backend/model-detail-llm").serve("backend/models-paginate").serve("backend/tool-detail-utility")
    platform.serve("backend/file-asset-detail")
    platform.route("GET", "backend", "/sdk/file-asset/{id}/children/recursive", StubResponse(body=[]))
    sse = ['data: {"choices":[{"index":0,"delta":{"content":"Hi"},"finish_reason":"stop"}]}', "", "data: [DONE]", ""]
    responses = iter(
        [
            StubResponse(body=load_recording("models/llm-run-success")["response"]["json"]),
            StubResponse(headers={"Content-Type": "text/event-stream"}, sse=sse),
            StubResponse(
                status=400, body={"error": "err.supplier_error", "supplierError": "bad input", "statusCode": 400}
            ),
        ]
    )
    platform.route("POST", "models", "/" + LLM_ID, lambda _r, _p: next(responses))

    aix.Agent.get(AGENT_ID).run("What is the capital of France?", show_progress=False)
    model = aix.Model.get(LLM_ID)
    model.run(text="hi")
    list(model.run_stream(text="hi"))
    with pytest.raises(APIError) as failure:
        model.run(text="hi")
    aix.Model.search(query="gpt")
    aix.Tool.get("66f423426eb563fa213a3531")
    aix.File.get("file-contract-1")
    return failure.value


def test_key_reaches_the_platform_only_as_the_auth_header(aix, platform: PlatformStub, canary: str) -> None:
    _every_flow(aix, platform)

    assert len(platform.requests) >= 10
    for request in platform.requests:
        assert request.url.startswith((BACKEND_URL, MODELS_ROOT_URL))
        assert canary not in request.url
        assert canary not in request.text, "key in the body of %s %s" % (request.method, request.url)
        assert request.headers.get("x-api-key") == canary


def test_key_is_never_logged_even_with_body_logging_on(
    aix, platform: PlatformStub, canary: str, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AIXPLAIN_LOG_BODIES", "1")
    caplog.set_level(logging.DEBUG)

    _every_flow(aix, platform)

    assert any("POST" in r.getMessage() for r in caplog.records), "request logging did not run"
    formatter = logging.Formatter("%(name)s %(levelname)s %(message)s")
    assert [r.name for r in caplog.records if canary in formatter.format(r)] == []


def test_errors_do_not_carry_the_key(aix, platform: PlatformStub, canary: str) -> None:
    error = _every_flow(aix, platform)

    assert canary not in str(error) and canary not in repr(error)
    assert canary not in repr(getattr(error, "response_data", ""))


def test_a_redirect_to_another_origin_drops_the_key(aix, platform: PlatformStub, canary: str) -> None:
    # #1040: requests' own redirect handling must not carry the auth header off the platform.
    platform.route(
        "GET",
        "backend",
        "/v2/models/{id}",
        StubResponse(status=302, headers={"Location": FOREIGN + "/collect"}, body=b""),
    )
    platform.route("GET", FOREIGN, "/collect", StubResponse(status=404, body={"message": "Not Found"}))

    with pytest.raises(Exception):  # noqa: B017  (a 404 from the foreign host, however the SDK reports it)
        aix.Model.get(LLM_ID)

    [foreign] = [r for r in platform.requests if r.url.startswith(FOREIGN)]
    assert "x-api-key" not in {k.lower() for k in foreign.headers}
    assert canary not in str(foreign.headers)


def test_a_poll_url_on_a_foreign_host_is_refused_before_any_request(aix, platform: PlatformStub) -> None:
    # #1040: the poll URL comes from the response body; an attacker-controlled
    # body must not make the SDK send the key elsewhere.
    platform.serve("backend/agent-detail")
    platform.route(
        "POST",
        "backend",
        "/v2/agents/{id}/run",
        StubResponse(status=201, body={"data": FOREIGN + "/sdk/agents/x/result", "requestId": "x"}),
    )

    with pytest.raises(UntrustedURLError):
        aix.Agent.get(AGENT_ID).run("hi", show_progress=False)

    assert not [r for r in platform.requests if r.url.startswith(FOREIGN)]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ENG-3782 finding (ENG-3761 BUG item 1): Aixplain.__init__ writes the caller's key into "
        "os.environ['TEAM_API_KEY'] and ['AIXPLAIN_API_KEY'] (aixplain/v2/core.py), so a process that "
        "serves several tenants keeps the last tenant's key in its environment."
    ),
)
def test_constructing_a_client_leaves_the_environment_alone(aix, canary: str) -> None:
    assert not [name for name, value in os.environ.items() if canary in value]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ENG-3782 finding (consequence of the os.environ write): a client built without an explicit key "
        "resolves TEAM_API_KEY/AIXPLAIN_API_KEY, which the previous tenant's client just wrote, so it "
        "authenticates as that tenant."
    ),
)
def test_a_later_keyless_client_does_not_inherit_the_previous_key(aix, canary: str) -> None:
    from aixplain import Aixplain

    assert Aixplain(backend_url=BACKEND_URL).api_key != canary
