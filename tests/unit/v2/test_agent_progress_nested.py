"""Progress display of a team agent's subagent steps (nested under ``delegate_task``)."""

from types import SimpleNamespace

from aixplain import AgentProgressTracker, ProgressFormat


def _tracker(fmt: ProgressFormat = ProgressFormat.LOGS, verbosity: int = 1) -> AgentProgressTracker:
    tracker = AgentProgressTracker(poll_func=lambda _: None, force_display=False)
    tracker.start(format=fmt, verbosity=verbosity)
    return tracker


def _response(steps):
    return SimpleNamespace(to_dict=lambda: {"data": {"steps": steps}})


def _model(step_id, agent, output=None, status="completed", credits=0.001):
    return {
        "step_id": step_id,
        "status": status,
        "agent": {"name": agent},
        "unit": {"name": "GPT-4o Mini", "type": "model"},
        "output": output,
        "used_credits": credits,
        "api_calls": 1,
    }


def _tool(step_id, agent, name, output=None, status="completed", credits=0.0):
    return {
        "step_id": step_id,
        "status": status,
        "agent": {"name": agent},
        "unit": {"name": name, "type": "tool"},
        "output": output,
        "used_credits": credits,
        "api_calls": 1,
    }


def _delegate(step_id, target, nested, status="completed", output="child answer", execution_id="949-abc"):
    step = _tool(step_id, "team", "delegate_task", output=output, status=status, credits=0.002)
    step["input"] = '{"agent_name": "%s", "task": "t"}' % target
    step["execution_id"] = execution_id
    step["steps"] = nested
    return step


def _lines(capsys):
    # A spinner line is overwritten in place with "\r"; keep what the terminal shows.
    return [line.split("\r")[-1] for line in capsys.readouterr().out.split("\n")]


def test_logs_nest_a_delegations_steps_under_it(capsys):
    """A delegation gets a header, its subagent steps indented under it, then its own completion line."""
    tracker = _tracker()
    nested = [
        _model("m1", "web_researcher", output="calling search"),
        _tool("t1", "web_researcher", "Tavily Web Search", output="ERROR: boom", status="failed"),
        _tool("t2", "web_researcher", "Tavily Web Search", output="3 results"),
    ]
    tracker.update(
        _response([_model("root-1", "team", output="delegating"), _delegate("d1", "web_researcher", nested)])
    )
    tracker.stop()

    lines = [line for line in _lines(capsys) if line.strip()]
    assert lines[0].startswith("✓ Step  1")
    assert lines[1].startswith("▸ Step  2") and "delegate_task → web_researcher" in lines[1]
    assert lines[2].startswith("  ✓ Step 2.1") and "web_researcher ⧈ GPT-4o Mini" in lines[2]
    assert lines[3].startswith("  ✗ Step 2.2") and "Tavily Web Search" in lines[3]
    assert lines[4].startswith("  ✓ Step 2.3")
    assert lines[5].startswith("✓ Step  2") and "delegate_task → web_researcher" in lines[5]


def test_logs_show_nested_steps_live_and_print_each_once(capsys):
    """Nested steps appear while the delegation runs, and each line is printed once across polls."""
    tracker = _tracker()
    running = _delegate("d1", "facts", [_model("m1", "facts", status="executing")], status="executing", output=None)
    tracker.update(_response([running]))
    done_child = _delegate("d1", "facts", [_model("m1", "facts", output="3 facts")], status="executing", output=None)
    tracker.update(_response([done_child]))
    tracker.update(_response([done_child]))
    tracker.update(_response([_delegate("d1", "facts", [_model("m1", "facts", output="3 facts")])]))
    tracker.stop()

    out = capsys.readouterr().out
    assert out.count("▸ Step  1") == 1
    assert out.count("✓ Step 1.1") == 1
    assert out.count("✓ Step  1") == 1


def test_same_child_ids_under_two_delegations_do_not_collide(capsys):
    """Child ids are only unique per delegation; two subagents may both report the same one."""
    tracker = _tracker()
    tracker.update(
        _response(
            [
                _delegate("d1", "a", [_model("m1", "a", output="from a")]),
                _delegate("d2", "b", [_model("m1", "b", output="from b")]),
            ]
        )
    )
    tracker.stop()

    out = capsys.readouterr().out
    assert "✓ Step 1.1" in out and "✓ Step 2.1" in out


def test_a_step_finished_by_status_without_output_is_marked_done(capsys):
    """A model step that only called tools has no output; its status still marks it done."""
    tracker = _tracker()
    tracker.update(_response([_model("m1", "team", output=None, status="completed")]))
    tracker.stop()

    assert "✓ Step  1" in capsys.readouterr().out


def test_execution_id_is_shown_from_verbosity_two(capsys):
    """The subagent's platform execution id is shown on the delegation header at verbosity 2+."""
    quiet, verbose = _tracker(verbosity=1), _tracker(verbosity=2)
    steps = [_delegate("d1", "facts", [], execution_id="949-xyz")]
    quiet.update(_response(steps))
    quiet.stop()
    assert "949-xyz" not in capsys.readouterr().out

    verbose.update(_response(steps))
    verbose.stop()
    assert "↳ execution 949-xyz" in capsys.readouterr().out


def test_totals_count_only_top_level_steps():
    """A delegation carries its subagent's total, so nested steps are never summed again."""
    tracker = _tracker()
    nested = [_model("m1", "facts", output="x", credits=0.5)]
    tracker.update(_response([_model("root-1", "team", output="y", credits=0.25), _delegate("d1", "facts", nested)]))
    tracker.stop()

    assert tracker._total_credits == 0.25 + 0.002
    assert tracker._total_api_calls == 2


def test_status_line_shows_the_deepest_active_step(capsys):
    """Status mode follows a running delegation down to the step its subagent is on."""
    tracker = _tracker(fmt=ProgressFormat.STATUS)
    nested = [
        _model("m1", "web_researcher", output="calling"),
        _tool("t1", "web_researcher", "Tavily Web Search", status="executing"),
    ]
    steps = tracker._parse_steps(
        _response([_delegate("d1", "web_researcher", nested, status="executing", output=None)])
    )
    tracker._refresh_status_display(steps)
    tracker.stop()

    line = capsys.readouterr().out.split("\r")[-1]
    assert "Step 1.2" in line
    assert "web_researcher ⚒ Tavily Web Search" in line


def test_steps_without_nesting_render_as_before(capsys):
    """Engines that send no nested steps render exactly as before."""
    tracker = _tracker()
    tracker.update(_response([_model("m1", "team", output="answer")]))
    tracker.stop()

    lines = [line for line in _lines(capsys) if line.strip()]
    assert len(lines) == 1 and lines[0].startswith("✓ Step  1")
    assert "▸" not in lines[0]


def test_parallel_delegations_keep_one_live_line_and_label_every_child(capsys):
    """With two delegations running at once, only the newest running step owns the live line."""
    tracker = _tracker()
    a = _delegate(
        "d1",
        "a",
        [_model("m1", "a", output="a done"), _tool("t1", "a", "search", status="executing")],
        status="executing",
        output=None,
    )
    b = _delegate("d2", "b", [_model("m1", "b", status="executing")], status="executing", output=None)
    tracker.update(_response([a, b]))
    tracker.stop()

    lines = [line for line in _lines(capsys) if line.strip()]
    assert lines[0].startswith("▸ Step  1") and lines[1].startswith("  ✓ Step 1.1")
    assert lines[2].startswith("▸ Step  2")
    # The single live line: the newest running step, a's search is still running but b is newer.
    assert lines[-1].lstrip().startswith(tuple("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")) and "Step 2.1" in lines[-1]
    assert sum("Step 1.2" in line for line in lines) == 0


def test_a_delegation_is_recognised_before_its_steps_arrive(capsys):
    """An engine may send the delegate step before its nested ``steps``; it still gets a header."""
    tracker = _tracker()
    early = _delegate("d1", "facts", [], status="executing", output=None)
    del early["steps"]
    tracker.update(_response([early]))
    tracker.update(_response([_delegate("d1", "facts", [_model("m1", "facts", output="3 facts")])]))
    tracker.stop()

    out = capsys.readouterr().out
    assert out.count("▸ Step  1") == 1
    assert "  ✓ Step 1.1" in out


def test_thought_dedup_and_details_use_the_nested_step_number(capsys):
    """A nested step's thought is keyed by its own number and indented with it."""
    tracker = _tracker(verbosity=3)
    top = {**_model("m0", "team", output="plan"), "thought": "same idea"}
    child = {**_model("m1", "facts", output="facts"), "thought": "child idea", "input": "subtask"}
    repeat = {**_model("m2", "team", output="final"), "thought": "child idea"}
    tracker.update(_response([top, _delegate("d1", "facts", [child]), repeat]))
    tracker.stop()

    out = capsys.readouterr().out
    assert "    ∷ child idea" in out
    assert "∷ [see Step 2.1]" in out
    assert "    ← Context" in out or "    ← Input" in out
    assert "    ← Query" not in out


def test_status_line_follows_the_delegation_still_running(capsys):
    """When a later sibling already finished, the status line stays on the one still working."""
    tracker = _tracker(fmt=ProgressFormat.STATUS)
    running = _delegate("d1", "a", [_tool("t1", "a", "search", status="executing")], status="executing", output=None)
    finished = _delegate("d2", "b", [_model("m1", "b", output="done")])
    tracker._refresh_status_display(tracker._parse_steps(_response([running, finished])))
    tracker.stop()

    assert "Step 1.1" in capsys.readouterr().out.split("\r")[-1]


def test_output_that_arrives_after_a_status_only_completion_is_still_shown(capsys):
    """A step marked done by status first and given its output later prints that output once."""
    tracker = _tracker(verbosity=3)
    tracker.update(_response([_model("m1", "team", output=None, status="completed")]))
    tracker.update(_response([_model("m1", "team", output="late answer", status="completed")]))
    tracker.update(_response([_model("m1", "team", output="late answer", status="completed")]))
    tracker.stop()

    assert capsys.readouterr().out.count("late answer") == 1
