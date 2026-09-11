"""Unit tests for v1 connection reuse in ``_request_with_retry`` (BUG-942 item 3).

``_request_with_retry`` used to build a fresh ``requests.Session`` inside the
per-request function, use it once and drop it (never ``close()``d), so every one
of the ~105 v1 call sites paid a full TLS handshake. A 5-minute v1 job polls ~44
times: ~44 handshakes where keep-alive needs one.

There is no socket here, so the offline proxy for "~1 TLS handshake, not ~100"
is "~1 ``Session``, not ~100" -- a session is what owns the connection pool.

The session is per *thread*, not per process: ``requests`` documents ``Session``
as not thread-safe, and v1 reaches this module from ``ThreadPoolExecutor`` pools.
A shared session would also share ``session.cookies``, so a ``Set-Cookie`` from
any host would persist process-wide.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import requests

from aixplain.utils import request_utils
from aixplain.utils.request_utils import _request_with_retry, get_session


class TestSessionReuse:
    """One session per thread, reused by every call on that thread."""

    def test_thread_session_exists(self):
        assert isinstance(get_session(), requests.Session)

    def test_a_hundred_calls_construct_no_new_session(self):
        """The acceptance criterion: ~1 pooled connection, not ~100."""
        session = get_session()
        with patch.object(session, "request", return_value=Mock()) as request:
            with patch("requests.Session") as session_ctor:
                for index in range(100):
                    _request_with_retry("get", f"https://example.com/poll/{index}")

        assert request.call_count == 100
        session_ctor.assert_not_called()

    def test_every_call_uses_the_same_session_object(self):
        # Session identity, observed through the public entry point.
        seen = []

        def capture(self, **kwargs):
            seen.append(id(self))
            return Mock()

        with patch.object(requests.Session, "request", capture):
            _request_with_retry("get", "https://example.com/a")
            _request_with_retry("get", "https://example.com/b")

        assert len(set(seen)) == 1


class TestThreadIsolation:
    """No mutable session state is shared across threads."""

    def test_each_thread_gets_its_own_session(self):
        sessions = []
        lock = threading.Lock()
        barrier = threading.Barrier(8)

        def collect():
            session = get_session()
            with lock:
                sessions.append(session)
            barrier.wait()  # keep all eight threads alive at once

        threads = [threading.Thread(target=collect) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(sessions) == 8
        assert len({id(session) for session in sessions}) == 8
        assert all(session is not get_session() for session in sessions)

    def test_a_worker_thread_reuses_its_own_session(self):
        """Pool workers are long-lived, so the reuse win survives per-thread state."""
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(get_session).result()
            second = pool.submit(get_session).result()

        assert first is second

    def test_a_cookie_set_on_one_thread_does_not_leak_to_another(self):
        """A ``Set-Cookie`` from any host used to persist process-wide."""

        def set_cookie():
            get_session().cookies.set("session", "leaked", domain="evil.example.com")

        thread = threading.Thread(target=set_cookie)
        thread.start()
        thread.join()

        assert "session" not in get_session().cookies


class TestPoolSizing:
    """A reused session needs a sized pool, or reuse is cancelled out.

    urllib3 defaults to 10/10 with ``block=False``: above 10 in-flight requests
    the adapter opens a connection, uses it once and *discards* it, logging
    "Connection pool is full" each time.
    """

    def test_adapter_pool_is_sized_explicitly(self):
        adapter = get_session().get_adapter("https://example.com")

        assert adapter._pool_connections == request_utils._POOL_CONNECTIONS
        assert adapter._pool_maxsize == request_utils._POOL_MAXSIZE

    def test_pool_is_larger_than_the_urllib3_default(self):
        assert request_utils._POOL_CONNECTIONS > 10
        assert request_utils._POOL_MAXSIZE > 10

    def test_value_reaches_urllib3(self):
        adapter = get_session().get_adapter("https://example.com")
        pool = adapter.poolmanager.connection_from_url("https://example.com")

        assert pool.pool.maxsize == request_utils._POOL_MAXSIZE

    def test_fifty_concurrent_checkouts_do_not_warn_about_a_full_pool(self, caplog):
        adapter = get_session().get_adapter("https://example.com")
        pool = adapter.poolmanager.connection_from_url("https://example.com")

        barrier = threading.Barrier(50)
        conns = [None] * 50

        def hold(index):
            conns[index] = pool._get_conn()
            barrier.wait()  # all 50 out at once
            pool._put_conn(conns[index])

        threads = [threading.Thread(target=hold, args=(i,)) for i in range(50)]
        with caplog.at_level("WARNING", logger="urllib3.connectionpool"):
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        assert not [r for r in caplog.records if "pool is full" in r.getMessage().lower()]


class TestRetryConfigPreserved:
    """The change is connection reuse only -- retry behaviour is untouched."""

    def test_https_adapter_carries_the_same_retry_config(self):
        adapter = get_session().get_adapter("https://example.com")

        assert adapter.max_retries.total == 5
        assert adapter.max_retries.backoff_factor == 0.1
        assert set(adapter.max_retries.status_forcelist) == {500, 502, 503, 504}

    def test_method_and_params_are_forwarded_unchanged(self):
        with patch.object(get_session(), "request", return_value=Mock()) as request:
            _request_with_retry("post", "https://example.com/x", headers={"a": "b"}, data="payload")

        assert request.call_args.kwargs == {
            "method": "POST",
            "url": "https://example.com/x",
            "headers": {"a": "b"},
            "data": "payload",
        }

    def test_method_is_upper_cased(self):
        with patch.object(get_session(), "request", return_value=Mock()) as request:
            _request_with_retry("get", "https://example.com/x")

        assert request.call_args.kwargs["method"] == "GET"

    def test_response_is_returned_unchanged(self):
        sentinel = Mock()

        with patch.object(get_session(), "request", return_value=sentinel):
            assert _request_with_retry("get", "https://example.com/x") is sentinel
