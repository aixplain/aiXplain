import os
import pytest


def is_v3_run() -> bool:
    """True when the suite is being routed through the V3 backend run service.

    V3 has no response-generation phase, so tests that assert presence of a
    response_generator step skip those assertions in V3 mode.
    """
    return os.getenv("AIXPLAIN_SERVICE_VERSION", "").upper() == "V3"


@pytest.fixture(scope="module")
def client():
    """Initialize Aixplain client with test configuration for v2 tests."""
    # Require credentials from environment variables for security
    api_key = os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")
    if not api_key:
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")

    backend_url = os.getenv("BACKEND_URL") or "https://dev-platform-api.aixplain.com"
    # V2 tests require V2 model URL - ensure we use /api/v2/ even if env has /api/v1/
    model_url = os.getenv("MODELS_RUN_URL") or "https://dev-models.aixplain.com/api/v2/execute"
    model_url = model_url.replace("/api/v1/", "/api/v2/")

    from aixplain import Aixplain

    return Aixplain(
        api_key=api_key,
        backend_url=backend_url,
        model_url=model_url,
    )


@pytest.fixture(scope="module")
def slack_token():
    """Get Slack token for integration tests."""
    # Require Slack token from environment variable for security
    token = os.getenv("SLACK_TOKEN")
    if not token:
        pytest.skip("SLACK_TOKEN environment variable is required for Slack integration tests")
    return token


@pytest.fixture(autouse=True)
def _inject_service_version(monkeypatch):
    """Route every Agent.run through a chosen serviceVersion when AIXPLAIN_SERVICE_VERSION is set.

    Why: lets the whole v2 functional suite exercise the new backend run service
    without editing each test. Tests that pass service_version explicitly win
    (setdefault), so unit-style coverage of the param is preserved.
    """
    sv = os.getenv("AIXPLAIN_SERVICE_VERSION")
    if not sv:
        return

    from aixplain.v2.agent import Agent
    from aixplain.v2.enums import ServiceVersion

    try:
        target = ServiceVersion(sv.upper())
    except ValueError:
        allowed = ", ".join(v.value for v in ServiceVersion)
        pytest.fail(f"AIXPLAIN_SERVICE_VERSION must be one of: {allowed}, got {sv!r}")

    original_run = Agent.run

    def patched_run(self, *args, **kwargs):
        kwargs.setdefault("service_version", target)
        return original_run(self, *args, **kwargs)

    monkeypatch.setattr(Agent, "run", patched_run)
