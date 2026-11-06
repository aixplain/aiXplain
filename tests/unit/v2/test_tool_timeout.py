"""Unit tests for the per-tool ``timeout`` override (ENG-3817).

The platform limits each agent call to a tool to a default it owns (per
model/integration definition, else the agent runtime's own). A user overrides it
per tool by setting ``timeout`` on the tool object before attaching it::

    tool = aix.Tool.get("...")
    tool.timeout = 30
    agent = aix.Agent(name="my-agent", tools=[tool])
    agent.save()                                  # persists timeout=30
"""

import warnings
from decimal import Decimal
from fractions import Fraction
from unittest.mock import Mock

import pytest

from aixplain import Agent, Integration, Model, Tool, ValidationError
from aixplain.v2.exceptions import ResourceError


def _ctx() -> Mock:
    """A mock client context that exposes the real Tool/Model resource classes."""
    ctx = Mock(client=Mock(), backend_url="https://platform-api.aixplain.com", api_key="k")
    ctx.Model = Model
    ctx.Tool = Tool
    return ctx


def _bound_agent(ctx: Mock):
    class BoundAgent(Agent):
        context = ctx

    return BoundAgent


def _with_timeout(obj, timeout):
    obj.timeout = timeout
    return obj


def _model(timeout=None) -> Model:
    return _with_timeout(Model(id="m1", name="translate"), timeout)


def _saved_tools(agent: Agent) -> list:
    agent.context = agent.context or Mock()
    return agent.build_save_payload()["tools"]


def _fetched_agent(tool_dict: dict) -> Agent:
    """An onboarded agent as ``Agent.get()`` leaves it: hydrated, with a saved-state baseline."""
    agent = _bound_agent(_ctx()).from_dict(
        {"name": "n", "description": "d", "tools": [tool_dict], "status": "onboarded"}
    )
    agent._update_saved_state()
    return agent


def _create_agent_with(tool, response_tool: dict) -> Agent:
    """Create a bound agent whose POST response echoes *response_tool* as its only tool."""
    ctx = _ctx()
    ctx.client.request.side_effect = lambda method, path, **kw: (
        {"id": "agent-1", "name": "a", "description": "d", "status": "onboarded", "tools": [response_tool]}
        if method == "post"
        else {}
    )
    ctx.client.get.side_effect = lambda *a, **k: {}
    agent = _bound_agent(ctx)(name="a", description="d", tools=[tool])
    agent.save()
    return agent


def _saved_agent(tool_dict: dict, put_response_tools=None):
    """A fetched, onboarded agent whose PUT echoes *put_response_tools* (omitted when None)."""
    ctx = _ctx()
    sent = []

    def request(method, path, **kw):
        if method == "put":
            sent.append(kw["json"])
            response = {"id": "agent-1", "name": "n", "description": "d", "status": "onboarded"}
            if put_response_tools is not None:
                response["tools"] = put_response_tools
            return response
        return {}

    ctx.client.request.side_effect = request
    ctx.client.get.side_effect = lambda *a, **k: {}
    agent = _bound_agent(ctx).from_dict(
        {"id": "agent-1", "name": "n", "description": "d", "tools": [tool_dict], "status": "onboarded"}
    )
    agent._update_saved_state()
    return agent, sent


class TestAsTool:
    def test_unset_timeout_is_omitted(self):
        assert "timeout" not in _model().as_tool()

    def test_model_timeout_serialized_as_float_seconds(self):
        timeout = _model(10).as_tool()["timeout"]
        assert timeout == 10.0
        assert isinstance(timeout, float)

    def test_tool_inherits_timeout(self):
        tool = _with_timeout(Tool(id="t1", name="air"), 2.5)
        tool.context = Mock()
        assert tool.as_tool()["timeout"] == 2.5

    def test_integration_inherits_timeout(self):
        assert _with_timeout(Integration(id="i1", name="air"), 10).as_tool()["timeout"] == 10.0

    def test_any_real_number_accepted(self):
        assert _model(Fraction(5, 2)).as_tool()["timeout"] == 2.5

    @pytest.mark.parametrize(
        "value",
        [0, -1, True, "10", float("inf"), float("nan"), 10**400],
        ids=["zero", "negative", "bool", "str", "inf", "nan", "overflow"],
    )
    def test_invalid_timeout_raises(self, value):
        with pytest.raises(ValidationError, match="positive number of seconds"):
            _model(value).as_tool()

    def test_decimal_accepted(self):
        assert _model(Decimal("2.5")).as_tool()["timeout"] == 2.5

    @pytest.mark.parametrize("value", [Decimal("NaN"), Decimal("sNaN"), Decimal("-1")], ids=["nan", "snan", "neg"])
    def test_invalid_decimal_raises(self, value):
        with pytest.raises(ValidationError, match="positive number of seconds"):
            _model(value).as_tool()

    def test_timeout_above_the_runtime_ceiling_warns(self):
        with pytest.warns(UserWarning, match="run ceiling"):
            assert _model(7200).as_tool()["timeout"] == 7200.0

    def test_timeout_at_the_runtime_ceiling_does_not_warn(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert _model(3600).as_tool()["timeout"] == 3600.0

    def test_timeout_not_sent_when_saving_the_model_itself(self):
        # Only the agent's tool entry carries it, not the asset's own payload.
        assert "timeout" not in _model(10).to_dict()


class TestBackendRecords:
    @pytest.mark.parametrize("raw", [10, "10s", {"value": 10}, 0], ids=["number", "text", "dict", "zero"])
    def test_backend_timeout_key_is_not_decoded(self, raw):
        # A platform default on the model record must not come back as the
        # user's override, and an unexpected shape must not break Model.get().
        model = Model.from_dict({"id": "m1", "name": "translate", "timeout": raw})
        assert model.timeout is None
        assert "timeout" not in model.as_tool()

    def test_create_response_keeps_the_callers_timeout(self):
        # The create response never carries it, so it must stay authoritative locally.
        model = _model(5)
        model.context = Mock()
        model.context.client.request.return_value = {"id": "new-1", "name": "translate", "timeout": 99}
        model._create("v2/models", {"name": "translate"})
        assert model.id == "new-1"
        assert model.timeout == 5


class TestAgentSave:
    def test_save_payload_carries_tool_timeout(self):
        agent = Agent(name="n", description="d", tools=[_model(10)])
        assert _saved_tools(agent)[0]["timeout"] == 10.0

    def test_save_payload_omits_unset_timeout(self):
        agent = Agent(name="n", description="d", tools=[_model()])
        assert "timeout" not in _saved_tools(agent)[0]

    @pytest.mark.parametrize("bound", [False, True], ids=["plain-agent", "client-agent"])
    @pytest.mark.parametrize("value", [-5, "10", "soon"], ids=["negative", "numeric-str", "text"])
    def test_caller_dict_tool_entry_is_validated(self, bound, value):
        # Caller input is strict on every path; only backend records are lenient.
        cls = _bound_agent(_ctx()) if bound else Agent
        agent = cls(name="n", description="d", tools=[{"id": "m1", "type": "model", "timeout": value}])
        with pytest.raises(ValidationError, match="positive number of seconds"):
            _saved_tools(agent)

    def test_dict_tool_entry_timeout_sent_as_float(self):
        agent = Agent(name="n", description="d", tools=[{"id": "m1", "type": "model", "timeout": 10}])
        assert _saved_tools(agent)[0]["timeout"] == 10.0

    @pytest.mark.parametrize("tool_type", ["model", "tool"])
    def test_fetched_agent_keeps_timeout_on_resave(self, tool_type):
        agent = _fetched_agent({"id": "x1", "type": tool_type, "name": "air", "timeout": 10})

        assert agent.tools[0].timeout == 10
        agent.tools[0].timeout = 30
        assert _saved_tools(agent)[0]["timeout"] == 30.0

    def test_stored_numeric_string_is_coerced(self):
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": "10"})
        assert agent.tools[0].timeout == 10.0

    @pytest.mark.parametrize("raw", [0, "soon", True], ids=["zero", "text", "bool"])
    def test_invalid_stored_timeout_is_dropped_so_the_agent_still_saves(self, raw):
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": raw})
        assert agent.tools[0].timeout is None
        assert "timeout" not in _saved_tools(agent)[0]

    def test_create_warns_when_the_platform_drops_the_timeout(self):
        with pytest.warns(UserWarning, match="did not store the timeout set on tool 'm1'"):
            agent = _create_agent_with(_model(5), {"id": "m1", "type": "model", "name": "translate"})
        # The caller's object, and its value, are kept.
        assert agent.tools[0].timeout == 5

    def test_create_does_not_warn_when_the_platform_stores_the_timeout(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            agent = _create_agent_with(_model(5), {"id": "m1", "type": "model", "name": "translate", "timeout": 5})
        assert agent.tools[0].timeout == 5


class TestClearingAStoredTimeout:
    # The platform keeps a stored timeout when a save omits the key (so a client
    # that does not know the field cannot erase it), so unsetting one the
    # platform stored has to be sent as an explicit None.

    @pytest.mark.parametrize("tool_type", ["model", "tool"])
    def test_unsetting_a_fetched_timeout_sends_none(self, tool_type):
        agent = _fetched_agent({"id": "x1", "type": tool_type, "name": "air", "timeout": 10})
        agent.tools[0].timeout = None
        saved = _saved_tools(agent)[0]
        assert "timeout" in saved
        assert saved["timeout"] is None

    def test_unsetting_a_timeout_saved_on_create_sends_none(self):
        agent = _create_agent_with(_model(5), {"id": "m1", "type": "model", "name": "translate", "timeout": 5})
        agent.tools[0].timeout = None
        saved = _saved_tools(agent)[0]
        assert "timeout" in saved
        assert saved["timeout"] is None

    def test_a_tool_the_platform_never_stored_a_timeout_for_omits_the_key(self):
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air"})
        assert "timeout" not in _saved_tools(agent)[0]

    def test_a_dict_entry_without_a_timeout_omits_the_key(self):
        # An omitted key keeps whatever the platform stored for that tool.
        agent = Agent(name="n", description="d", tools=[{"id": "m1", "type": "model"}])
        assert "timeout" not in _saved_tools(agent)[0]

    @pytest.mark.parametrize("tool_type", ["model", "tool"])
    @pytest.mark.parametrize("bound", [False, True], ids=["plain-agent", "client-agent"])
    def test_a_dict_entry_with_timeout_none_sends_none(self, bound, tool_type):
        # Both agent types send the clear the caller asked for.
        cls = _bound_agent(_ctx()) if bound else Agent
        agent = cls(name="n", description="d", tools=[{"id": "m1", "type": tool_type, "timeout": None}])
        saved = _saved_tools(agent)[0]
        assert "timeout" in saved
        assert saved["timeout"] is None

    def test_a_stored_null_is_not_taken_for_a_clear(self, caplog):
        # The backend returns null for a tool with no timeout; that is unset,
        # not an invalid value to warn about.
        with caplog.at_level("WARNING"):
            agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": None})
        assert "timeout" not in _saved_tools(agent)[0]
        assert "Ignoring invalid stored timeout" not in caplog.text

    def test_clearing_marks_the_agent_modified(self):
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": 10})
        agent.tools[0].timeout = None
        assert agent.is_modified is True


class TestSaveRaisesValidationError:
    # save() runs inside with_hooks, which turns other exceptions into a
    # ResourceError; the timeout check has to run before it.

    @pytest.mark.parametrize("value", [0, -1, True, "10", float("nan")], ids=["zero", "neg", "bool", "str", "nan"])
    def test_tool_object(self, value):
        agent, sent = _saved_agent({"id": "x1", "type": "model", "name": "air"})
        agent.tools[0].timeout = value
        with pytest.raises(ValidationError, match="positive number of seconds") as raised:
            agent.save()
        assert not isinstance(raised.value, ResourceError)
        assert sent == []

    @pytest.mark.parametrize("bound", [False, True], ids=["plain-agent", "client-agent"])
    def test_dict_tool(self, bound):
        cls = _bound_agent(_ctx()) if bound else Agent
        agent = cls(name="n", description="d", tools=[{"id": "m1", "type": "model", "timeout": -5}])
        with pytest.raises(ValidationError, match="positive number of seconds"):
            agent.save()


class TestUpdateResponse:
    # The PUT response carries the platform's copy of the tools, the same as
    # a create's, so an update is checked too.

    def test_update_warns_when_the_platform_drops_the_timeout(self):
        agent, sent = _saved_agent(
            {"id": "x1", "type": "model", "name": "air"},
            put_response_tools=[{"id": "x1", "type": "model", "name": "air", "timeout": None}],
        )
        agent.tools[0].timeout = 5
        with pytest.warns(UserWarning, match="did not store the timeout set on tool 'x1'"):
            agent.save()
        assert sent[0]["tools"][0]["timeout"] == 5.0
        assert agent.tools[0].timeout == 5

    def test_update_does_not_warn_when_the_platform_stores_it(self):
        agent, _ = _saved_agent(
            {"id": "x1", "type": "model", "name": "air"},
            put_response_tools=[{"id": "x1", "type": "model", "name": "air", "timeout": 5}],
        )
        agent.tools[0].timeout = 5
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            agent.save()
        assert agent.tools[0]._platform_timeout == 5

    def test_a_value_the_platform_dropped_is_not_recorded_as_stored(self):
        agent, _ = _saved_agent(
            {"id": "x1", "type": "model", "name": "air"},
            put_response_tools=[{"id": "x1", "type": "model", "name": "air"}],
        )
        agent.tools[0].timeout = 5
        with pytest.warns(UserWarning):
            agent.save()
        # Nothing was stored, so there is nothing to clear.
        agent.tools[0].timeout = None
        assert "timeout" not in _saved_tools(agent)[0]

    def test_a_stored_value_is_recorded_so_unsetting_it_clears_it(self):
        agent, _ = _saved_agent(
            {"id": "x1", "type": "model", "name": "air"},
            put_response_tools=[{"id": "x1", "type": "model", "name": "air", "timeout": 5}],
        )
        agent.tools[0].timeout = 5
        agent.save()
        agent.tools[0].timeout = None
        assert _saved_tools(agent)[0]["timeout"] is None

    def test_a_response_without_tools_records_the_sent_value(self):
        agent, _ = _saved_agent({"id": "x1", "type": "model", "name": "air"})
        agent.tools[0].timeout = 5
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            agent.save()
        agent.tools[0].timeout = None
        assert _saved_tools(agent)[0]["timeout"] is None


class TestIsModified:
    def test_timeout_change_marks_agent_modified(self):
        # Unlike input values there is no run-time override for it, so an
        # unsaved change must not be silently ignored by run().
        agent = _fetched_agent({"id": "x1", "type": "model", "name": "air", "timeout": 10})
        assert agent.is_modified is False
        agent.tools[0].timeout = 30
        assert agent.is_modified is True

    def test_timeout_change_on_a_dict_tool_marks_agent_modified(self):
        agent = Agent(name="n", description="d", tools=[{"id": "m1", "type": "model", "timeout": 10}])
        agent._update_saved_state()
        assert agent.is_modified is False
        agent.tools[0]["timeout"] = 30
        assert agent.is_modified is True
