"""Replay recorded aiXplain platform responses under the SDK (ENG-3782, layers 1, 2 and 5).

ENG-3761 found SDK fixes whose tests mocked ``client.request`` with a body the
author typed: #983 (diagnostic codes nested under ``data``), BUG-1092/#1146
(sort fields the backend ignores), #1142. Here the SDK's real ``requests``
session sends the request and only the bytes come from a recording under
``tests/contract/recordings``: ``requests.adapters.HTTPAdapter.send`` is
patched, below the SDK's retry adapter and trusted-origin checks, so those run
for real too.

Hosts are never-resolvable ``*.test`` names, so a request that escapes the
stub fails on DNS instead of reaching a real platform. A recording's body may
say ``{backend}``, ``{models}``, ``{models_root}`` or a captured path
parameter such as ``{request_id}``; they are filled in when it is served.
"""

from __future__ import annotations

import io
import json
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Mapping, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

import requests
from requests.adapters import HTTPAdapter
from requests.structures import CaseInsensitiveDict

BACKEND_URL = "https://platform.contract.test"
MODELS_ROOT_URL = "https://models.contract.test"
MODELS_RUN_URL = MODELS_ROOT_URL + "/api/v2/execute"
RECORDINGS_DIR = Path(__file__).resolve().parents[1] / "contract" / "recordings"

# ``models`` routes are relative to the execute endpoint; ``models_root`` to the host.
_HOSTS = {"backend": BACKEND_URL, "models": MODELS_RUN_URL, "models_root": MODELS_ROOT_URL}


@dataclass
class RecordedRequest:
    method: str
    url: str
    headers: Dict[str, str]
    body: bytes

    @property
    def path(self) -> str:
        return urlsplit(self.url).path

    @property
    def query(self) -> Dict[str, List[str]]:
        return parse_qs(urlsplit(self.url).query)

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.body) if self.body else None


@dataclass
class StubResponse:
    status: int = 200
    body: Any = None
    headers: Dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json"})
    sse: Optional[List[str]] = None

    def content(self) -> bytes:
        if self.sse is not None:
            return "".join(line + "\n" for line in self.sse).encode("utf-8")
        if self.body is None:
            return b""
        if isinstance(self.body, (bytes, bytearray)):
            return bytes(self.body)
        if isinstance(self.body, str):
            return self.body.encode("utf-8")
        return json.dumps(self.body).encode("utf-8")


Responder = Callable[[RecordedRequest, Dict[str, str]], StubResponse]


def fill(value: Any, params: Optional[Mapping[str, str]] = None) -> Any:
    """Fill host placeholders and captured path parameters into a recorded value."""
    if isinstance(value, str):
        out = value.replace("{backend}", BACKEND_URL).replace("{models_root}", MODELS_ROOT_URL)
        out = out.replace("{models}", MODELS_RUN_URL)
        for key, item in (params or {}).items():
            out = out.replace("{" + key + "}", item)
        return out
    if isinstance(value, list):
        return [fill(v, params) for v in value]
    if isinstance(value, dict):
        return {k: fill(v, params) for k, v in value.items()}
    return value


def _path_regex(path: str) -> "re.Pattern[str]":
    pieces = re.split(r"\{(\w+)\}", path)
    pattern = "".join(re.escape(p) if i % 2 == 0 else "(?P<%s>[^/?]+)" % p for i, p in enumerate(pieces))
    return re.compile("^" + pattern + "$")


def load_recording(name: str) -> Dict[str, Any]:
    """``tests/contract/recordings/<name>.json`` as a dict."""
    data: Dict[str, Any] = json.loads((RECORDINGS_DIR / (name + ".json")).read_text(encoding="utf-8"))
    return data


def recording_response(name: str) -> StubResponse:
    response = load_recording(name)["response"]
    return StubResponse(
        status=int(response.get("status", 200)),
        body=response.get("json"),
        headers=dict(response.get("headers") or {"Content-Type": "application/json"}),
        sse=response.get("sse"),
    )


@dataclass
class _Route:
    method: str
    host: str
    regex: "re.Pattern[str]"
    responders: List[Responder]
    where: Dict[str, str]
    match: Optional[Callable[[RecordedRequest], bool]]
    served: int = 0


class PlatformStub:
    """Route table answering the SDK's requests from recordings or callables."""

    def __init__(self) -> None:
        self._routes: List[_Route] = []
        self.requests: List[RecordedRequest] = []
        self.unmatched: List[RecordedRequest] = []

    def serve(
        self,
        name: str,
        then: Optional[List[Any]] = None,
        where: Optional[Dict[str, str]] = None,
        match: Optional[Callable[[RecordedRequest], bool]] = None,
    ) -> "PlatformStub":
        """Answer the recording's endpoint with it (then with each of ``then``; the last repeats)."""
        endpoint = load_recording(name)["endpoint"]
        responders: List[Responder] = []
        for item in [name, *(then or [])]:
            if isinstance(item, StubResponse):
                responders.append(lambda _r, _p, item=item: item)
            else:
                responders.append(lambda _r, p, item=item: _filled(recording_response(item), p))
        return self._add(
            _Route(
                endpoint["method"].upper(),
                endpoint["host"],
                _path_regex(endpoint["path"]),
                responders,
                dict(where or {}),
                match,
            )
        )

    def route(self, method: str, host: str, path: str, responder: Any) -> "PlatformStub":
        fn: Responder = responder if callable(responder) else (lambda _r, _p: responder)
        return self._add(_Route(method.upper(), host, _path_regex(path), [fn], {}, None))

    def _add(self, route: _Route) -> "PlatformStub":
        # The first matching route answers, so a route registered after an
        # unconditional one for the same endpoint would never be served and
        # its test would pass without exercising it.
        for earlier in self._routes:
            if (earlier.method, earlier.host, earlier.regex.pattern) == (route.method, route.host, route.regex.pattern):
                if not earlier.where and earlier.match is None:
                    raise ValueError(
                        "%s %s %s is already answered by an earlier route; this one would never be served"
                        % (route.method, route.host, route.regex.pattern)
                    )
        self._routes.append(route)
        return self

    def answer(self, request: RecordedRequest) -> StubResponse:
        self.requests.append(request)
        parts = urlsplit(request.url)
        for route in self._routes:
            base = urlsplit(_HOSTS.get(route.host, route.host))
            if (parts.scheme, parts.netloc) != (base.scheme, base.netloc) or request.method != route.method:
                continue
            prefix = base.path.rstrip("/")
            if prefix and not parts.path.startswith(prefix):
                continue
            found = route.regex.match(parts.path[len(prefix) :] or "/")
            if found is None or any(found.groupdict().get(k) != v for k, v in route.where.items()):
                continue
            if route.match is not None and not route.match(request):
                continue
            index = min(route.served, len(route.responders) - 1)
            route.served += 1
            return route.responders[index](request, found.groupdict())
        self.unmatched.append(request)
        raise requests.ConnectionError("platform stub has no recording for %s %s" % (request.method, request.url))

    def sent(self, method: Optional[str] = None, path_contains: str = "") -> List[RecordedRequest]:
        return [
            r
            for r in self.requests
            if (method is None or r.method == method.upper()) and path_contains in r.path and r not in self.unmatched
        ]

    @contextmanager
    def mounted(self) -> Iterator["PlatformStub"]:
        stub = self
        original = HTTPAdapter.send

        def send(
            adapter: HTTPAdapter, prepared: requests.PreparedRequest, *args: Any, **kwargs: Any
        ) -> requests.Response:
            body = prepared.body or b""
            if isinstance(body, str):
                body = body.encode("utf-8")
            recorded = RecordedRequest(
                str(prepared.method).upper(),
                str(prepared.url),
                {k: str(v) for k, v in prepared.headers.items()},
                bytes(body),
            )
            answer = stub.answer(recorded)
            response = requests.Response()
            response.status_code = answer.status
            response.headers = CaseInsensitiveDict(answer.headers)
            response.raw = io.BytesIO(answer.content())
            response.url = recorded.url
            response.request = prepared
            response.encoding = "utf-8"
            response.reason = "OK" if answer.status < 400 else "Error"
            return response

        HTTPAdapter.send = send  # type: ignore[method-assign]
        try:
            yield self
        finally:
            HTTPAdapter.send = original  # type: ignore[method-assign]


def _filled(response: StubResponse, params: Dict[str, str]) -> StubResponse:
    return StubResponse(
        status=response.status,
        body=fill(response.body, params),
        headers=response.headers,
        sse=fill(response.sse, params) if response.sse is not None else None,
    )


def hosts() -> Tuple[str, str]:
    """(backend_url, model_url) to construct the SDK client with."""
    return BACKEND_URL, MODELS_RUN_URL
