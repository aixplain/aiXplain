"""Fixtures for the recorded platform contract suite (ENG-3782, layer 1).

The SDK talks to the platform through its real ``requests`` session; only the
bytes come from ``tests/contract/recordings``. ``platform`` fails the test if
the SDK sent a request no recording answers.
"""

import uuid
from typing import Iterator
from unittest import mock

import pytest

from aixplain.utils import user_info_utils

from tests.support.platform_replay import BACKEND_URL, MODELS_RUN_URL, PlatformStub

_ENV = (
    "TEAM_API_KEY",
    "AIXPLAIN_API_KEY",
    "BACKEND_URL",
    "MODELS_RUN_URL",
    "PIPELINES_RUN_URL",
    "AIXPLAIN_TRUSTED_HOSTS",
)


@pytest.fixture(autouse=True)
def _stub_ipinfo() -> Iterator[None]:
    """Agent runs attach run metadata from ipinfo.io (BUG-1096); a third party, not the platform."""
    with mock.patch.object(user_info_utils, "_fetch_ipinfo", return_value={"ip": "203.0.113.7", "loc": "0,0"}):
        yield


@pytest.fixture
def api_key() -> str:
    """Not 64 hex characters: that is a real key's shape, which the secret scanners flag."""
    return "contract-key-" + uuid.uuid4().hex[:12]


@pytest.fixture
def aix(api_key: str, monkeypatch: pytest.MonkeyPatch):
    """A real SDK client pointed at the stub hosts.

    ``Aixplain.__init__`` writes the key into ``os.environ``; registering the
    variables with monkeypatch first makes teardown remove that write.
    """
    from aixplain import Aixplain

    for name in _ENV:
        monkeypatch.setenv(name, "unset-by-contract-fixture")
        monkeypatch.delenv(name)
    return Aixplain(api_key=api_key, backend_url=BACKEND_URL, model_url=MODELS_RUN_URL)


@pytest.fixture
def platform() -> Iterator[PlatformStub]:
    stub = PlatformStub()
    with stub.mounted():
        yield stub
    assert not stub.unmatched, "requests no recording answers: " + ", ".join(
        "%s %s" % (r.method, r.url) for r in stub.unmatched
    )
