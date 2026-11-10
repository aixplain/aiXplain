"""The fault proxies themselves (ENG-3782, layer 3).

The socket backend is checked against a local echo server. The toxiproxy
backend is checked against its REST API shape with a mock transport; CI runs
the whole stage against a real toxiproxy server (TOXIPROXY_URL).
"""

from __future__ import annotations

import socket
import threading
import time
from collections.abc import Iterator

import pytest

from tests.fault.fault_proxy import SocketProxyBackend, ToxiproxyBackend


@pytest.fixture
def echo_port() -> Iterator[int]:
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    stop = threading.Event()

    def serve() -> None:
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except OSError:
                continue
            with conn:
                while data := conn.recv(65536):
                    conn.sendall(data)

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    yield int(server.getsockname()[1])
    stop.set()
    server.close()


@pytest.fixture
def proxy() -> Iterator[SocketProxyBackend]:
    backend = SocketProxyBackend()
    yield backend
    backend.close()


def _roundtrip(port: int, payload: bytes, *, timeout: float = 5.0) -> tuple[bytes, float]:
    started = time.monotonic()
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as conn:
        conn.sendall(payload)
        received = b""
        while len(received) < len(payload):
            chunk = conn.recv(65536)
            if not chunk:
                break
            received += chunk
    return received, time.monotonic() - started


def test_clean_proxy_passes_bytes_through(proxy: SocketProxyBackend, echo_port: int) -> None:
    port = proxy.add("echo", echo_port)
    assert _roundtrip(port, b"hello")[0] == b"hello"


def test_latency_delays_the_response(proxy: SocketProxyBackend, echo_port: int) -> None:
    port = proxy.add("echo", echo_port)
    proxy.toxic("echo", "latency", latency=400)
    data, elapsed = _roundtrip(port, b"hello")
    assert data == b"hello" and elapsed >= 0.38


def test_limit_data_closes_after_n_bytes(proxy: SocketProxyBackend, echo_port: int) -> None:
    port = proxy.add("echo", echo_port)
    proxy.toxic("echo", "limit_data", bytes=3)
    assert _roundtrip(port, b"hello")[0] == b"hel"


def test_bandwidth_slows_the_body(proxy: SocketProxyBackend, echo_port: int) -> None:
    port = proxy.add("echo", echo_port)
    proxy.toxic("echo", "bandwidth", rate=1)  # 1 KB/s
    data, elapsed = _roundtrip(port, b"x" * 1536)
    assert len(data) == 1536 and elapsed >= 1.2


def test_timeout_toxic_holds_the_line_silent(proxy: SocketProxyBackend, echo_port: int) -> None:
    port = proxy.add("echo", echo_port)
    proxy.toxic("echo", "timeout", timeout=0)
    with pytest.raises(socket.timeout):
        _roundtrip(port, b"hello", timeout=0.5)


def test_reset_peer_resets_the_connection(proxy: SocketProxyBackend, echo_port: int) -> None:
    port = proxy.add("echo", echo_port)
    proxy.toxic("echo", "reset_peer", timeout=0)
    with pytest.raises((ConnectionResetError, BrokenPipeError, ConnectionAbortedError)):
        _roundtrip(port, b"hello" * 1000)


def test_toxiproxy_backend_speaks_the_rest_api(requests_mock) -> None:
    base = "http://toxiproxy.test:8474"
    requests_mock.get(base + "/version", text="2.12.0")
    requests_mock.delete(base + "/proxies/platform", status_code=204)
    requests_mock.post(base + "/proxies", status_code=201, json={"name": "platform", "listen": "127.0.0.1:41234"})
    requests_mock.post(base + "/proxies/platform/toxics", status_code=200, json={})
    requests_mock.get(base + "/proxies/platform/toxics", json=[{"name": "timeout_downstream"}])
    requests_mock.delete(base + "/proxies/platform/toxics/timeout_downstream", status_code=204)

    backend = ToxiproxyBackend(base)
    assert backend.add("platform", 8080) == 41234
    backend.toxic("platform", "timeout", timeout=0)
    backend.clear("platform")
    backend.close()

    calls = [(r.method, r.path, r.json() if r.body else None) for r in requests_mock.request_history]
    assert (
        "POST",
        "/proxies",
        {"name": "platform", "listen": "127.0.0.1:0", "upstream": "127.0.0.1:8080", "enabled": True},
    ) in calls
    assert (
        "POST",
        "/proxies/platform/toxics",
        {
            "name": "timeout_downstream",
            "type": "timeout",
            "stream": "downstream",
            "toxicity": 1.0,
            "attributes": {"timeout": 0},
        },
    ) in calls
    assert ("DELETE", "/proxies/platform/toxics/timeout_downstream", None) in calls
