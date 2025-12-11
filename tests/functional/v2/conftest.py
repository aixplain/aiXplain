import os
import pytest


@pytest.fixture(scope="module")
def client():
    """Initialize Aixplain client with test configuration for v2 tests."""
    # Require credentials from environment variables for security
    api_key = os.getenv("TEAM_API_KEY")
    if not api_key:
        pytest.skip(
            "TEAM_API_KEY environment variable is required for functional tests"
        )

    backend_url = os.getenv("BACKEND_URL") or "https://dev-platform-api.aixplain.com"
    model_url = (
        os.getenv("MODELS_RUN_URL") or "https://dev-models.aixplain.com/api/v2/execute"
    )

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
        pytest.skip(
            "SLACK_TOKEN environment variable is required for Slack integration tests"
        )
    return token
