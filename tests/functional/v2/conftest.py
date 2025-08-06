import os
import pytest


@pytest.fixture(scope="module")
def client():
    """Initialize Aixplain client with test configuration for v2 tests."""
    api_key = os.getenv("TEAM_API_KEY")
    if not api_key:
        pytest.skip("TEAM_API_KEY environment variable not set")

    backend_url = os.getenv("BACKEND_URL", "https://dev-platform-api.aixplain.com/")
    model_url = os.getenv(
        "MODELS_RUN_URL", "https://dev-models.aixplain.com/api/v1/execute"
    )

    from aixplain import Aixplain

    return Aixplain(
        api_key=api_key,
        backend_url=backend_url,
        model_url=model_url,
    )
