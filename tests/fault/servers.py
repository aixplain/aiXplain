"""Socket-serving platform stubs for the fault-injection stage (ENG-3782, layer 3).

``PlatformHTTPServer`` answers HTTP on a real port from a ``PlatformStub``
route table, so the recorded responses of the contract suite are what the
code under test receives, through toxiproxy, over TCP. ``FaultResponse``
adds the HTTP-level faults a TCP proxy cannot produce: a connection closed
before any response, headers followed by a stall, a body cut short, and
503/429 bursts (plain ``StubResponse`` statuses with headers).

A server plays one role (``backend`` or ``models``): it maps each request onto
that role's canonical stub host so the stub's routes match, and rewrites the
canonical hosts in response bodies to the proxy's address, so a recorded poll
URL leads back through the proxy.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import requests

from tests.support.platform_replay import (
    BACKEND_URL,
    MODELS_ROOT_URL,
    PlatformStub,
    RecordedRequest,
    StubResponse,
)

__all__ = ["FaultResponse", "PlatformHTTPServer"]

_CANONICAL = {"backend": BACKEND_URL, "models": MODELS_ROOT_URL}


@dataclass
class FaultResponse(StubResponse):
    """A ``StubResponse`` with socket behaviour only a real server can produce."""

    close_without_response: bool = False
    stall_after_headers_s: float = 0.0
    truncate_body_after: int | None = None
    delay_s: float = 0.0


class PlatformHTTPServer:
    """One platform role served from ``stub`` on 127.0.0.1:<port>."""

    def __init__(self, stub: PlatformStub, role: str) -> None:
        self.stub = stub
        self.role = role
        self.public_origins: dict[str, str] = {}
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self._httpd.daemon_threads = True
        self.port = int(self._httpd.server_address[1])
        self._thread = threading.Thread(target=self._httpd.serve_forever, name=f"stub-{role}", daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()

    def _rewrite(self, body: bytes) -> bytes:
        for canonical, public in self.public_origins.items():
            body = body.replace(canonical.encode(), public.encode())
        return body

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        server = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args: Any) -> None:  # keep test output readable
                return

            def _handle(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                recorded = RecordedRequest(
                    method=self.command,
                    url=_CANONICAL[server.role] + self.path,
                    headers={k.lower(): v for k, v in self.headers.items()},
                    body=body,
                )
                try:
                    answer = server.stub.answer(recorded)
                except requests.ConnectionError as exc:
                    answer = StubResponse(status=599, body={"stub": str(exc)})
                fault = answer if isinstance(answer, FaultResponse) else None
                if fault is not None and fault.delay_s:
                    time.sleep(fault.delay_s)
                if fault is not None and fault.close_without_response:
                    self.close_connection = True
                    self.connection.close()
                    return
                payload = server._rewrite(answer.content())
                self.send_response(answer.status)
                for key, value in answer.headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.flush()
                if fault is not None and fault.stall_after_headers_s:
                    time.sleep(fault.stall_after_headers_s)
                    self.close_connection = True
                    return
                if fault is not None and fault.truncate_body_after is not None:
                    self.wfile.write(payload[: fault.truncate_body_after])
                    self.wfile.flush()
                    self.close_connection = True
                    self.connection.close()
                    return
                self.wfile.write(payload)

            do_GET = _handle
            do_POST = _handle
            do_PUT = _handle
            do_DELETE = _handle

        return Handler
