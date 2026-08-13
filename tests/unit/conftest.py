import socket
from contextlib import closing

import pytest


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
