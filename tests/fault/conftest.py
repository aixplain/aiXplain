"""Fixtures for the SDK's out-of-process fault-injection stage (ENG-3782, layer 3).

The platform stub's backend and models roles are real HTTP servers behind a
fault proxy (toxiproxy when ``TOXIPROXY_URL`` is set, as in CI; otherwise the
in-repo socket proxy). ``FAULT_INJECTION_REQUIRE=1`` turns a missing proxy
into a failure instead of a skip.
"""

import os
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator, List
from unittest import mock

import pytest

from aixplain.utils import user_info_utils
from tests.fault.fault_proxy import FaultProxy, SocketProxyBackend, ToxiproxyBackend
from tests.fault.servers import PlatformHTTPServer
from tests.support.platform_replay import BACKEND_URL, MODELS_ROOT_URL, PlatformStub

READ_TIMEOUT_S = 2.0
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
    with mock.patch.object(user_info_utils, "_fetch_ipinfo", return_value={"ip": "203.0.113.7", "loc": "0,0"}):
        yield


@pytest.fixture(scope="session")
def fault_proxy() -> Iterator[FaultProxy]:
    url = os.environ.get("TOXIPROXY_URL")
    if url:
        try:
            backend: FaultProxy = ToxiproxyBackend(url)
        except Exception as exc:
            if os.environ.get("FAULT_INJECTION_REQUIRE") == "1":
                pytest.fail("FAULT_INJECTION_REQUIRE=1 but toxiproxy at %s is unreachable: %s" % (url, exc))
            pytest.skip("toxiproxy at %s is unreachable" % url)
    else:
        backend = SocketProxyBackend()
    yield backend
    backend.close()


@dataclass
class Faulty:
    stub: PlatformStub
    proxy: FaultProxy
    backend: str
    models: str
    client: Any = None
    servers: List[PlatformHTTPServer] = field(default_factory=list)

    def toxic(self, which: str, kind: str, **attributes: Any) -> None:
        self.proxy.toxic(getattr(self, which), kind, **attributes)


@pytest.fixture
def faulty(fault_proxy: FaultProxy, monkeypatch: pytest.MonkeyPatch) -> Iterator[Faulty]:
    """A real SDK client whose backend and models hosts are stub servers behind a fault proxy."""
    from aixplain import Aixplain

    for name in _ENV:
        monkeypatch.setenv(name, "unset-by-fault-fixture")
        monkeypatch.delenv(name)
    monkeypatch.setenv("AIXPLAIN_ALLOW_INSECURE_URLS", "1")  # loopback http
    monkeypatch.setenv("AIXPLAIN_HTTP_READ_TIMEOUT", str(READ_TIMEOUT_S))
    stub = PlatformStub()
    suffix = uuid.uuid4().hex[:6]
    servers = [PlatformHTTPServer(stub, "backend"), PlatformHTTPServer(stub, "models")]
    backend_port = fault_proxy.add("sdk-backend-" + suffix, servers[0].port)
    models_port = fault_proxy.add("sdk-models-" + suffix, servers[1].port)
    origins = {BACKEND_URL: "http://127.0.0.1:%d" % backend_port, MODELS_ROOT_URL: "http://127.0.0.1:%d" % models_port}
    for server in servers:
        server.public_origins = origins
    faulty = Faulty(stub, fault_proxy, "sdk-backend-" + suffix, "sdk-models-" + suffix, servers=servers)
    faulty.client = Aixplain(
        api_key="fault-key-" + suffix,
        backend_url=origins[BACKEND_URL],
        model_url=origins[MODELS_ROOT_URL] + "/api/v2/execute",
    )
    yield faulty
    for name in (faulty.backend, faulty.models):
        fault_proxy.clear(name)
    for server in servers:
        server.close()
