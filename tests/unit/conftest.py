import socket
from contextlib import closing
from unittest import mock

import pytest

from aixplain.utils import user_info_utils

#: Deterministic stand-in for the ``https://ipinfo.io/json`` lookup. Many unit
#: tests build an agent run payload, and ``build_run_metadata`` reaches the real
#: service once per process through ``_fetch_ipinfo``'s ``lru_cache``. Stubbing
#: it keeps the credential-free unit suite off the network and the derived
#: ``metaData`` stable.
IPINFO_STUB = {
    "ip": "203.0.113.7",
    "country": "US",
    "loc": "37.7749,-122.4194",
    "timezone": "America/Los_Angeles",
}


@pytest.fixture(scope="session", autouse=True)
def _stub_ipinfo():
    """Patch out the one external call a plain unit run would otherwise make."""
    with mock.patch.object(user_info_utils, "_fetch_ipinfo", return_value=dict(IPINFO_STUB)):
        yield


@pytest.fixture
def blackhole_url():
    """A listener that completes the handshake and never answers.

    ``listen()`` without ``accept()`` still completes the TCP handshake from the
    kernel backlog, so the connect succeeds and the read blocks — the production
    failure mode an unbounded request turns into a permanent stall (LB draining,
    NAT blackhole, half-open socket).

    Sandboxed environments may forbid opening a listening socket at all; that is
    an environment limit, not a regression, so it skips rather than errors.
    """
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        try:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
        except OSError as e:
            pytest.skip(f"cannot open a loopback listener in this environment: {e}")
        yield f"http://127.0.0.1:{sock.getsockname()[1]}/blackhole"
