"""TCP fault proxies for the out-of-process fault-injection stage (ENG-3782, layer 3).

Shared with aixplain-agents tests/fault/fault_proxy.py (toxiproxy client on
``requests`` here, the SDK's own HTTP library). Two interchangeable backends
behind one small interface:

* ``ToxiproxyBackend`` drives a running toxiproxy server through its REST API.
  CI runs this one (``TOXIPROXY_URL``), so the faults come from the same tool
  the incident reviews (PROD-2954) reasoned about.
* ``SocketProxyBackend`` is an asyncio TCP proxy in a background thread that
  implements the same toxics with the same names and attributes. It lets the
  suite run where no toxiproxy server is available (a developer laptop).

Either way the faults are real: the code under test talks to a real socket,
its timeouts and retries run on the real clock, and a stall or a reset happens
in the kernel, not in a patched function. The in-process PROD-2954 tests
cannot cover that.

Toxics (``stream`` is ``"downstream"``, server to client, by default):

* ``latency``    ``{"latency": ms, "jitter": ms}``: delay each chunk.
* ``bandwidth``  ``{"rate": KB/s}``: cap throughput (a slow body).
* ``timeout``    ``{"timeout": ms}``: drop all data; close after ``timeout`` ms
  (0 keeps the connection open and silent until the toxic is removed).
* ``reset_peer`` ``{"timeout": ms}``: reset the connection (RST) after ``timeout`` ms.
* ``limit_data`` ``{"bytes": n}``: close the connection after ``n`` bytes.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

import requests

__all__ = ["FaultProxy", "SocketProxyBackend", "ToxiproxyBackend"]


class FaultProxy(Protocol):
    name: str

    def add(self, name: str, upstream_port: int, upstream_host: str = "127.0.0.1") -> int:
        """Create proxy ``name`` to the upstream; return the local port to connect to."""

    def toxic(self, name: str, kind: str, *, stream: str = "downstream", **attributes: Any) -> None:
        """Add a toxic to proxy ``name``."""

    def clear(self, name: str) -> None:
        """Remove every toxic from proxy ``name``."""

    def close(self) -> None:
        """Remove every proxy this backend created."""


# ---------------------------------------------------------------------------
# toxiproxy
# ---------------------------------------------------------------------------


class ToxiproxyBackend:
    """A toxiproxy server (https://github.com/Shopify/toxiproxy), via its REST API."""

    name = "toxiproxy"

    def __init__(self, api_url: str, *, session: requests.Session | None = None) -> None:
        self._base = api_url.rstrip("/")
        self._http = session or requests.Session()
        self._http.get(self._base + "/version", timeout=5).raise_for_status()
        self._proxies: list[str] = []

    def add(self, name: str, upstream_port: int, upstream_host: str = "127.0.0.1") -> int:
        self._http.delete("%s/proxies/%s" % (self._base, name), timeout=5)
        response = self._http.post(
            self._base + "/proxies",
            json={
                "name": name,
                "listen": "127.0.0.1:0",
                "upstream": "%s:%s" % (upstream_host, upstream_port),
                "enabled": True,
            },
            timeout=5,
        )
        response.raise_for_status()
        self._proxies.append(name)
        return int(response.json()["listen"].rsplit(":", 1)[1])

    def toxic(self, name: str, kind: str, *, stream: str = "downstream", **attributes: Any) -> None:
        response = self._http.post(
            "%s/proxies/%s/toxics" % (self._base, name),
            json={
                "name": "%s_%s" % (kind, stream),
                "type": kind,
                "stream": stream,
                "toxicity": 1.0,
                "attributes": attributes,
            },
            timeout=5,
        )
        response.raise_for_status()

    def clear(self, name: str) -> None:
        for toxic in self._http.get("%s/proxies/%s/toxics" % (self._base, name), timeout=5).json():
            self._http.delete("%s/proxies/%s/toxics/%s" % (self._base, name, toxic["name"]), timeout=5)

    def close(self) -> None:
        for name in self._proxies:
            self._http.delete("%s/proxies/%s" % (self._base, name), timeout=5)
        self._proxies.clear()


# ---------------------------------------------------------------------------
# in-repo socket proxy
# ---------------------------------------------------------------------------


@dataclass
class _Toxic:
    kind: str
    stream: str
    attributes: dict[str, Any]


@dataclass
class _Proxy:
    upstream: tuple[str, int]
    server: asyncio.base_events.Server | None = None
    toxics: list[_Toxic] = field(default_factory=list)
    connections: set[asyncio.StreamWriter] = field(default_factory=set)

    def active(self, stream: str, kind: str) -> _Toxic | None:
        return next((t for t in self.toxics if t.stream == stream and t.kind == kind), None)


def _reset(writer: asyncio.StreamWriter) -> None:
    """Close with RST instead of FIN: SO_LINGER on, linger time 0."""
    sock = writer.get_extra_info("socket")
    if sock is not None:
        with contextlib.suppress(OSError):
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
    writer.transport.abort()


class SocketProxyBackend:
    """Asyncio TCP proxies with toxiproxy's toxics, in a background thread."""

    name = "socket-proxy"

    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="fault-proxy", daemon=True)
        self._thread.start()
        self._proxies: dict[str, _Proxy] = {}

    def _call(self, coro: Any) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=10)

    def add(self, name: str, upstream_port: int, upstream_host: str = "127.0.0.1") -> int:
        proxy = _Proxy(upstream=(upstream_host, upstream_port))
        self._proxies[name] = proxy

        async def start() -> int:
            proxy.server = await asyncio.start_server(lambda r, w: self._serve(proxy, r, w), host="127.0.0.1", port=0)
            return int(proxy.server.sockets[0].getsockname()[1])

        port: int = self._call(start())
        return port

    def toxic(self, name: str, kind: str, *, stream: str = "downstream", **attributes: Any) -> None:
        proxy = self._proxies[name]
        proxy.toxics = [t for t in proxy.toxics if not (t.kind == kind and t.stream == stream)]
        proxy.toxics.append(_Toxic(kind, stream, dict(attributes)))
        if kind == "reset_peer":
            for writer in list(proxy.connections):
                self._loop.call_soon_threadsafe(self._schedule_reset, writer, attributes.get("timeout", 0))

    def clear(self, name: str) -> None:
        self._proxies[name].toxics = []

    def close(self) -> None:
        async def stop() -> None:
            for proxy in self._proxies.values():
                if proxy.server is not None:
                    proxy.server.close()
                for writer in list(proxy.connections):
                    writer.transport.abort()

        with contextlib.suppress(Exception):
            self._call(stop())
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)

    # -- per connection -------------------------------------------------------

    def _schedule_reset(self, writer: asyncio.StreamWriter, timeout_ms: float) -> None:
        self._loop.call_later(max(0.0, timeout_ms) / 1000, _reset, writer)

    async def _serve(self, proxy: _Proxy, client_r: asyncio.StreamReader, client_w: asyncio.StreamWriter) -> None:
        proxy.connections.add(client_w)
        reset = proxy.active("downstream", "reset_peer") or proxy.active("upstream", "reset_peer")
        if reset is not None:
            self._schedule_reset(client_w, float(reset.attributes.get("timeout", 0)))
        try:
            upstream_r, upstream_w = await asyncio.open_connection(*proxy.upstream)
        except OSError:
            _reset(client_w)
            proxy.connections.discard(client_w)
            return
        closed = asyncio.Event()
        pumps = [
            asyncio.create_task(self._pump(proxy, "upstream", client_r, upstream_w, client_w, closed)),
            asyncio.create_task(self._pump(proxy, "downstream", upstream_r, client_w, client_w, closed)),
        ]
        await closed.wait()
        for task in pumps:
            task.cancel()
        for writer in (client_w, upstream_w):
            with contextlib.suppress(Exception):
                writer.close()
        proxy.connections.discard(client_w)

    async def _pump(
        self,
        proxy: _Proxy,
        stream: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        client_w: asyncio.StreamWriter,
        closed: asyncio.Event,
    ) -> None:
        sent = 0
        try:
            while True:
                data = await reader.read(16384)
                if not data:
                    break
                timeout = proxy.active(stream, "timeout")
                if timeout is not None:
                    # Drop the data; close after the timeout, or hold the line silent.
                    ms = float(timeout.attributes.get("timeout", 0))
                    if ms > 0:
                        await asyncio.sleep(ms / 1000)
                        break
                    # Toxics change from the test thread, outside this loop, so poll.
                    while proxy.active(stream, "timeout") is not None:  # noqa: ASYNC110
                        await asyncio.sleep(0.05)
                    continue
                latency = proxy.active(stream, "latency")
                if latency is not None:
                    await asyncio.sleep(float(latency.attributes.get("latency", 0)) / 1000)
                limit = proxy.active(stream, "limit_data")
                if limit is not None:
                    allowed = int(limit.attributes.get("bytes", 0)) - sent
                    if allowed <= 0:
                        break
                    data = data[:allowed]
                bandwidth = proxy.active(stream, "bandwidth")
                if bandwidth is not None:
                    rate = max(1.0, float(bandwidth.attributes.get("rate", 1))) * 1024  # bytes per second
                    for start in range(0, len(data), 256):
                        piece = data[start : start + 256]
                        writer.write(piece)
                        await writer.drain()
                        await asyncio.sleep(len(piece) / rate)
                else:
                    writer.write(data)
                    await writer.drain()
                sent += len(data)
                if limit is not None and sent >= int(limit.attributes.get("bytes", 0)):
                    break
        except (ConnectionError, asyncio.IncompleteReadError, OSError):
            pass
        finally:
            closed.set()


def connect_ok(port: int, host: str = "127.0.0.1", deadline_s: float = 5.0) -> bool:
    """Whether a TCP connection to ``host:port`` opens within ``deadline_s``."""
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        with contextlib.suppress(OSError), socket.create_connection((host, port), timeout=0.5):
            return True
        time.sleep(0.05)
    return False
