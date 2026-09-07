"""Unit tests for the minimal v1 ``UnboundLocalError`` fixes (BUG-941).

v1 is no longer maintained, so these fixes are line-level only: a handler that
already builds the documented failure value is made to *return* it, and every
name an ``except`` block reads is bound before its ``try``.

Four sites, all reproduced before the fix:

* ``call_run_endpoint`` -- the request handler fell through to ``r.status_code``,
  which is unbound when the request itself raised (``UnboundLocalError: 'r'``);
* ``call_run_endpoint`` -- a 2xx body that is not JSON left ``resp`` on its
  ``"unspecified error"`` sentinel, and ``resp.get`` then raised ``AttributeError``;
* ``build_payload`` -- ``copy.deepcopy`` is the first statement in its ``try`` and
  can itself raise ``TypeError`` (``UnboundLocalError: 'parametersTemp'``);
* ``Pipeline.poll`` -- ``resp = r.json()`` is the first statement in its ``try``
  and the handler reads ``resp`` (``UnboundLocalError: 'resp'``).

The non-2xx + non-JSON path already worked (the sentinel flows into
``get_error_from_status_code``); ``test_502_non_json_body_keeps_status_code_message``
guards it against regression.
"""

import threading
from unittest.mock import Mock, patch

import pytest
import requests

from aixplain.enums import ResponseStatus
from aixplain.v1.modules.model.utils import build_payload, call_run_endpoint
from aixplain.v1.modules.pipeline.asset import Pipeline
from aixplain.v1.modules.pipeline.response import PipelineResponse

UTILS_REQUEST = "aixplain.v1.modules.model.utils._request_with_retry"
PIPELINE_REQUEST = "aixplain.v1.modules.pipeline.asset._request_with_retry"


def _assert_failed_shape(response):
    """The failure contract ``call_run_endpoint``'s docstring promises."""
    assert isinstance(response, dict)
    assert response["status"] == "FAILED"
    assert response["completed"] is True
    assert isinstance(response["error_message"], str)
    assert response["error_message"]


def _json_error_response(status_code):
    """A response whose body cannot be decoded, as a 502 HTML page cannot."""
    response = Mock(status_code=status_code)
    response.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
    return response


class TestCallRunEndpointRequestFailure:
    """The request itself raises: the documented FAILED dict, never a crash."""

    @pytest.mark.parametrize(
        "error",
        [
            # The ticket's own repro uses the *builtin* ConnectionError, which is
            # not a requests.exceptions.RequestException.
            ConnectionError("boom"),
            requests.exceptions.ConnectionError("connection reset"),
            requests.exceptions.Timeout("read timed out"),
            requests.exceptions.SSLError("certificate verify failed"),
            OSError("dns lookup failed"),
        ],
        ids=["builtin-connection", "requests-connection", "timeout", "ssl", "oserror"],
    )
    def test_transport_error_returns_failed(self, error):
        """Every transport failure yields the documented FAILED dict."""
        with patch(UTILS_REQUEST, side_effect=error):
            response = call_run_endpoint("https://example.com/run", "api-key", {"data": "x"})
        _assert_failed_shape(response)

    def test_programming_errors_still_propagate(self):
        """A genuine bug in our own code must not be laundered into FAILED."""
        with patch(UTILS_REQUEST, side_effect=AttributeError("typo")):
            with pytest.raises(AttributeError):
                call_run_endpoint("https://example.com/run", "api-key", {"data": "x"})


class TestCallRunEndpointNonJsonBody:
    """The request succeeds but the body is not JSON."""

    def test_2xx_non_json_body_returns_failed(self):
        """A 2xx body we cannot decode is a failure, not an AttributeError."""
        with patch(UTILS_REQUEST, return_value=_json_error_response(200)):
            response = call_run_endpoint("https://example.com/run", "api-key", {"data": "x"})
        _assert_failed_shape(response)

    def test_502_non_json_body_keeps_status_code_message(self):
        """Regression guard: the status-code-mapped message must survive."""
        with patch(UTILS_REQUEST, return_value=_json_error_response(502)):
            response = call_run_endpoint("https://example.com/run", "api-key", {"data": "x"})
        _assert_failed_shape(response)
        assert "502" in response["error_message"]

    def test_real_non_json_response_via_requests_mock(self, requests_mock):
        """Exercises requests' own JSONDecodeError, not a Mock's ValueError."""
        url = "https://example.com/run"
        requests_mock.post(url, status_code=200, text="<html>502 Bad Gateway</html>")
        response = call_run_endpoint(url, "api-key", {"data": "x"})
        _assert_failed_shape(response)

    def test_2xx_json_body_still_succeeds(self):
        """The happy path is untouched."""
        response = Mock(status_code=200)
        response.json.return_value = {"status": "IN_PROGRESS", "data": "https://example.com/poll/1"}
        with patch(UTILS_REQUEST, return_value=response):
            result = call_run_endpoint("https://example.com/run", "api-key", {"data": "x"})
        assert result == {"status": "IN_PROGRESS", "url": "https://example.com/poll/1", "completed": False}


class TestBuildPayloadDeepcopyFailure:
    """``copy.deepcopy`` raising must not take out the serialization fallback."""

    def test_non_copyable_parameter_still_builds_payload(self):
        """A non-copyable parameter must not raise UnboundLocalError."""
        try:
            payload = build_payload("some data", {"lock": threading.Lock()})
        except UnboundLocalError:  # pragma: no cover - the bug under test
            pytest.fail("build_payload raised UnboundLocalError from its fallback")
        except TypeError:
            # json.dumps legitimately cannot serialize a lock; that error is the
            # caller's to see. Only UnboundLocalError is the defect.
            pass
        else:
            assert isinstance(payload, str)


class TestPipelinePollNonJsonBody:
    """``Pipeline.poll`` returns a FAILED PipelineResponse for an undecodable body."""

    @staticmethod
    def _pipeline():
        pipeline = Pipeline.__new__(Pipeline)
        pipeline.api_key = "api-key"
        pipeline.id = "pipeline-id"
        return pipeline

    def test_non_json_body_returns_failed_pipeline_response(self):
        """An undecodable poll body yields PipelineResponse(FAILED)."""
        with patch(PIPELINE_REQUEST, return_value=_json_error_response(502)):
            response = self._pipeline().poll("https://example.com/poll/1")
        assert isinstance(response, PipelineResponse)
        assert response.status is ResponseStatus.FAILED

    def test_json_array_body_returns_failed_pipeline_response(self):
        """A JSON array binds ``resp`` to a non-dict; ``.pop`` then raised TypeError."""
        response = Mock(status_code=200)
        response.json.return_value = ["a", "b"]
        with patch(PIPELINE_REQUEST, return_value=response):
            result = self._pipeline().poll("https://example.com/poll/1")
        assert isinstance(result, PipelineResponse)
        assert result.status is ResponseStatus.FAILED

    def test_successful_poll_unaffected(self):
        """The happy path still maps onto the SUCCESS status."""
        response = Mock(status_code=200)
        response.json.return_value = {"status": "SUCCESS", "elapsed_time": 12, "data": []}
        with patch(PIPELINE_REQUEST, return_value=response):
            result = self._pipeline().poll("https://example.com/poll/1")
        assert result.status is ResponseStatus.SUCCESS

    def test_v1_response_version_returns_raw_dict(self):
        """``response_version="v1"`` still returns the raw dict."""
        response = Mock(status_code=200)
        response.json.return_value = {"status": "SUCCESS", "data": []}
        with patch(PIPELINE_REQUEST, return_value=response):
            result = self._pipeline().poll("https://example.com/poll/1", response_version="v1")
        assert result == {"status": "SUCCESS", "data": []}
