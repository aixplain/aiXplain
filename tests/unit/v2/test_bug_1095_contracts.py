"""Unit tests for BUG-1095: error-contract, timeout and boundary defects in v2.

Each class pins one finding:

* ``with_hooks`` keeps the ``ResourceError`` rewrap but no longer drops the
  wrapped ``APIError``'s ``status_code`` / ``response_data`` or its cause.
* ``run()`` rejects a bad ``timeout`` / ``wait_time`` *before* the POST, so a
  bad argument no longer bills a run and then crashes.
* A poll ``TimeoutError`` carries ``poll_url`` / ``request_id``, so the billed
  job is not orphaned.
* An integration poll timeout raises instead of reading as "no actions".
* ``create_retry_session`` honours ``0`` / ``[]``.
* ``save()`` warns on unknown attributes; ``Page`` indexes; ``clone()`` shares
  the context; RLM parallel mode survives an empty context.
"""

import builtins
import warnings
from dataclasses import dataclass
from unittest.mock import Mock, patch

import pytest
from dataclasses_json import dataclass_json

from aixplain import Agent, Model
from aixplain.v2.client import (
    DEFAULT_RETRY_BACKOFF_FACTOR,
    DEFAULT_RETRY_STATUS_FORCELIST,
    DEFAULT_RETRY_TOTAL,
    create_retry_session,
)
from aixplain.v2.exceptions import APIError, ResourceError, TimeoutError
from aixplain.v2.integration import ActionMixin
from aixplain.v2.resource import BaseResource, Page
from aixplain.v2.rlm import RLM

BACKEND_URL = "https://platform-api.aixplain.com"
POLL_URL = f"{BACKEND_URL}/sdk/agents/exec-1/result"


def _bound(cls, **kwargs):
    """Instantiate *cls* bound to a mocked context."""

    @dataclass_json
    @dataclass
    class Bound(cls):
        pass

    instance = Bound(**kwargs)
    instance.context = Mock()
    instance.context.backend_url = BACKEND_URL
    instance.context.client.retry_total = DEFAULT_RETRY_TOTAL
    return instance


# ---------------------------------------------------------------------------
# with_hooks: keep the rewrap, keep the details
# ---------------------------------------------------------------------------


class TestWithHooksPreservesApiErrorDetails:
    def test_save_failure_keeps_status_code_response_data_and_cause(self):
        resource = _bound(BaseResource, id="r-1", name="r")
        resource.RESOURCE_PATH = "sdk/things"
        original = APIError("conflict", status_code=409, response_data={"message": "conflict"})
        resource.context.client.request = Mock(side_effect=original)

        with pytest.raises(ResourceError) as excinfo:
            resource.save()

        err = excinfo.value
        assert str(err) == "Failed to save resource: conflict"
        assert err.status_code == 409
        assert err.response_data == {"message": "conflict"}
        assert err.__cause__ is original

    def test_non_api_error_gets_none_details(self):
        resource = _bound(BaseResource, id="r-1", name="r")
        resource.RESOURCE_PATH = "sdk/things"
        resource.context.client.request = Mock(side_effect=RuntimeError("boom"))

        with pytest.raises(ResourceError) as excinfo:
            resource.save()

        assert excinfo.value.status_code is None
        assert excinfo.value.response_data is None
        assert isinstance(excinfo.value.__cause__, RuntimeError)

    def test_resource_error_defaults_exist_on_plain_instances(self):
        err = ResourceError("x")
        assert err.status_code is None
        assert err.response_data is None


# ---------------------------------------------------------------------------
# Validate timeout / wait_time before the POST
# ---------------------------------------------------------------------------


# ``None`` is absent here on purpose: Model drops ``None`` kwargs while merging
# its dynamic attributes, so ``timeout=None`` already means "default" there.
# The base validator's ``None`` handling is pinned separately below.
BAD_TIMEOUTS = [0, -1, "10", True, float("nan")]
BAD_WAIT_TIMES = [-1, "1", True, float("nan")]


class TestRunValidatesBudgetBeforePost:
    @pytest.mark.parametrize("timeout", BAD_TIMEOUTS)
    def test_model_async_run_rejects_bad_timeout_without_posting(self, timeout):
        model = _bound(Model, id="m-1", name="m")
        with patch.object(Model, "is_sync_only", False), patch.object(model, "_submit_with_retries") as submit:
            with pytest.raises(ValueError, match="timeout"):
                model.run(text="hi", timeout=timeout)
        submit.assert_not_called()

    @pytest.mark.parametrize("wait_time", BAD_WAIT_TIMES)
    def test_model_async_run_rejects_bad_wait_time_without_posting(self, wait_time):
        model = _bound(Model, id="m-1", name="m")
        with patch.object(Model, "is_sync_only", False), patch.object(model, "_submit_with_retries") as submit:
            with pytest.raises(ValueError, match="wait_time"):
                model.run(text="hi", wait_time=wait_time)
        submit.assert_not_called()

    @pytest.mark.parametrize("timeout", [0, -1])
    def test_model_sync_only_run_rejects_bad_timeout_without_posting(self, timeout):
        model = _bound(Model, id="m-1", name="m")
        with patch.object(Model, "is_sync_only", True), patch.object(model, "_run_sync_v2") as run_sync:
            with pytest.raises(ValueError, match="timeout"):
                model.run(text="hi", timeout=timeout)
        run_sync.assert_not_called()

    def test_wait_time_zero_is_accepted(self):
        model = _bound(Model, id="m-1", name="m")
        done = Model.RESPONSE_CLASS.from_dict({"status": "SUCCESS", "completed": True, "data": "ok"})
        with (
            patch.object(Model, "is_sync_only", False),
            patch.object(model, "_submit_with_retries", return_value=done) as submit,
        ):
            result = model.run(text="hi", wait_time=0, timeout=5)
        submit.assert_called_once()
        assert result.data == "ok"

    @pytest.mark.parametrize("timeout", [0, -5, "10"])
    def test_agent_run_rejects_bad_timeout_without_posting(self, timeout):
        agent = _bound(Agent, id="a-1", name="a")
        with patch.object(agent, "_submit_with_retries") as submit:
            with pytest.raises(ValueError, match="timeout"):
                agent.run("hi", timeout=timeout)
        submit.assert_not_called()

    def test_base_validator_rejects_none_but_agent_accepts_it(self):
        agent = _bound(Agent, id="a-1", name="a")
        assert agent._validate_poll_kwargs({"timeout": None}) is None  # does not raise
        with pytest.raises(ValueError):
            _bound(Model, id="m-1", name="m")._validate_poll_kwargs({"timeout": None})

    @pytest.mark.parametrize("kwargs", [{"timeout": 0}, {"wait_time": None}, {"wait_time": -1}])
    def test_agent_session_run_rejects_bad_budget_before_add_message(self, kwargs):
        agent = _bound(Agent, id="a-1", name="a")
        session = Mock()
        with patch.object(agent, "_resolve_session", return_value=session):
            with pytest.raises(ValueError):
                agent.run("hi", session=session, **kwargs)
        session.add_message.assert_not_called()


# ---------------------------------------------------------------------------
# Poll TimeoutError carries poll_url / request_id
# ---------------------------------------------------------------------------


class TestPollTimeoutCarriesHandles:
    def test_timeout_error_is_still_a_builtin_timeout(self):
        err = TimeoutError("t", poll_url="u", request_id="r")
        assert isinstance(err, builtins.TimeoutError)
        assert (err.poll_url, err.request_id) == ("u", "r")
        assert TimeoutError("t").poll_url is None

    def test_sync_poll_timeout_carries_poll_url(self):
        agent = _bound(Agent, id="a-1", name="a")
        with pytest.raises(TimeoutError) as excinfo:
            agent.sync_poll(POLL_URL, timeout=0)
        assert excinfo.value.poll_url == POLL_URL
        assert str(excinfo.value) == "Operation timed out after 0 seconds"

    def test_run_timeout_carries_request_id(self):
        model = _bound(Model, id="m-1", name="m")
        submitted = Model.RESPONSE_CLASS.from_dict(
            {"status": "IN_PROGRESS", "completed": False, "url": POLL_URL, "requestId": "req-1"}
        )
        submitted.request_id = "req-1"
        with (
            patch.object(Model, "is_sync_only", False),
            patch.object(model, "_submit_with_retries", return_value=submitted),
            patch.object(model, "sync_poll", side_effect=TimeoutError("timed out", poll_url=POLL_URL)),
        ):
            with pytest.raises(TimeoutError) as excinfo:
                model.run(text="hi", timeout=5)
        assert excinfo.value.poll_url == POLL_URL
        assert excinfo.value.request_id == "req-1"

    def test_model_sync_only_timeout_carries_request_id(self):
        model = _bound(Model, id="m-1", name="m")
        in_progress = Model.RESPONSE_CLASS.from_dict(
            {"status": "IN_PROGRESS", "completed": False, "url": f"{BACKEND_URL}/sdk/runs/abc"}
        )
        in_progress.request_id = "req-2"
        with (
            patch.object(Model, "is_sync_only", True),
            patch.object(model, "_run_sync_v2", return_value=in_progress),
            patch.object(model, "sync_poll", side_effect=TimeoutError("timed out")),
        ):
            with pytest.raises(TimeoutError) as excinfo:
                model.run(text="hi", timeout=5)
        assert excinfo.value.request_id == "req-2"

    def test_session_run_timeout_carries_request_id(self):
        agent = _bound(Agent, id="a-1", name="a")
        session = Mock()
        session.id = "s-1"
        session.add_message.return_value = Mock(request_id="req-3")
        with (
            patch.object(agent, "_resolve_session", return_value=session),
            patch.object(agent, "_apply_run_overrides_to_session"),
            patch.object(agent, "_build_tool_overrides", return_value=None),
            patch.object(agent, "sync_poll", side_effect=TimeoutError("timed out", poll_url=POLL_URL)),
        ):
            with pytest.raises(TimeoutError) as excinfo:
                agent.run("hi", session=session, timeout=5)
        assert excinfo.value.request_id == "req-3"
        assert excinfo.value.poll_url == POLL_URL

    def test_session_run_defaults_wait_time_when_absent(self):
        agent = _bound(Agent, id="a-1", name="a")
        session = Mock()
        session.id = "s-1"
        session.add_message.return_value = Mock(request_id="req-3")
        with (
            patch.object(agent, "_resolve_session", return_value=session),
            patch.object(agent, "_apply_run_overrides_to_session"),
            patch.object(agent, "_build_tool_overrides", return_value=None),
            patch.object(agent, "sync_poll", side_effect=TimeoutError("timed out")) as sync_poll,
        ):
            with pytest.raises(TimeoutError):
                agent.run("hi", session=session, timeout=5)
        assert sync_poll.call_args.kwargs["wait_time"] == 0.5


# ---------------------------------------------------------------------------
# Integration poll timeout raises instead of returning None / []
# ---------------------------------------------------------------------------


@dataclass
class _Actions(ActionMixin):
    pass


class TestIntegrationPollTimeout:
    def test_poll_for_data_raises_with_poll_url(self):
        actions = _Actions()
        actions.context = Mock()
        with pytest.raises(TimeoutError) as excinfo:
            actions._poll_for_data({"completed": False, "data": POLL_URL}, timeout=0)
        assert excinfo.value.poll_url == POLL_URL
        actions.context.client.request.assert_not_called()

    def test_list_actions_propagates_the_timeout(self):
        actions = _Actions()
        actions.context = Mock()
        actions.id = "tool-1"
        actions.context.client.request = Mock(return_value={"completed": False, "data": POLL_URL})
        with (
            patch.object(_Actions, "build_run_url", create=True, return_value=POLL_URL),
            patch.object(_Actions, "_poll_for_data", side_effect=TimeoutError("t", poll_url=POLL_URL)),
        ):
            with pytest.raises(TimeoutError):
                actions.list_actions()


# ---------------------------------------------------------------------------
# create_retry_session honours falsy settings
# ---------------------------------------------------------------------------


def _retry(session):
    return session.get_adapter("https://").max_retries


class TestRetrySessionHonoursFalsyValues:
    def test_zero_and_empty_are_kept(self):
        retry = _retry(create_retry_session(total=0, backoff_factor=0, status_forcelist=[]))
        assert retry.total == 0
        assert retry.backoff_factor == 0
        assert list(retry.status_forcelist) == []

    def test_none_falls_back_to_defaults(self):
        retry = _retry(create_retry_session(total=None, backoff_factor=None, status_forcelist=None))
        assert retry.total == DEFAULT_RETRY_TOTAL
        assert retry.backoff_factor == DEFAULT_RETRY_BACKOFF_FACTOR
        assert list(retry.status_forcelist) == list(DEFAULT_RETRY_STATUS_FORCELIST)


# ---------------------------------------------------------------------------
# save() warns on unknown attributes
# ---------------------------------------------------------------------------


class TestSaveWarnsOnUnknownAttributes:
    def _resource(self):
        resource = _bound(BaseResource, name="r")
        resource.RESOURCE_PATH = "sdk/things"
        resource.context.client.request = Mock(return_value={"id": "new-id", "name": "r"})
        return resource

    def test_typo_warns(self):
        resource = self._resource()
        with pytest.warns(UserWarning, match="descripton"):
            resource.save(descripton="typo")

    def test_known_attribute_does_not_warn(self):
        resource = self._resource()
        resource.context.client.request.return_value = {"id": "new-id", "name": "r", "description": "ok"}
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            resource.save(description="ok")
        assert resource.description == "ok"

    def test_agent_as_draft_option_does_not_warn(self):
        assert "as_draft" in Agent._SAVE_OPTION_KWARGS


# ---------------------------------------------------------------------------
# Page indexing and length
# ---------------------------------------------------------------------------


class TestPageIndexing:
    def test_int_slice_len_and_attribute_access(self):
        page = Page(results=["a", "b", "c"], page_number=0, page_total=1, total=3)
        assert page[0] == "a"
        assert page[-1] == "c"
        assert page[1:] == ["b", "c"]
        assert len(page) == 3
        assert page["total"] == 3

    def test_empty_page_stays_truthy(self):
        page = Page(results=[], page_number=0, page_total=0, total=0)
        assert len(page) == 0
        assert bool(page) is True


# ---------------------------------------------------------------------------
# clone() shares the context
# ---------------------------------------------------------------------------


class TestCloneSharesContext:
    def test_clone_shares_context_but_copies_state(self):
        resource = _bound(BaseResource, id="r-1", name="orig")
        cloned = resource.clone(name="copy")
        assert cloned.context is resource.context
        assert cloned.id is None
        assert cloned.name == "copy"
        assert resource.name == "orig"

    def test_nested_resources_share_the_context(self):
        resource = _bound(BaseResource, id="r-1", name="orig")
        child = _bound(BaseResource, id="c-1", name="child")
        child.context = resource.context
        resource.path = [child]  # any field holding a nested resource
        cloned = resource.clone()
        assert cloned.path[0] is not child
        assert cloned.path[0].context is resource.context


# ---------------------------------------------------------------------------
# RLM parallel mode with an empty context
# ---------------------------------------------------------------------------


class TestRlmEmptyContext:
    @pytest.mark.parametrize("context", [[], {}, ""])
    def test_empty_context_takes_single_call_path(self, context):
        rlm = RLM(name="r")
        rlm._used_credits = 0.0
        with (
            patch.object(rlm, "_get_worker"),
            patch.object(rlm, "_get_worker_context_tokens", return_value=8000),
            patch.object(rlm, "_worker_call", return_value="answer") as worker,
        ):
            result = rlm._run_parallel(context, "q", "r", start_time=0.0)
        assert result.status == "SUCCESS", result.error_message
        worker.assert_called_once()
