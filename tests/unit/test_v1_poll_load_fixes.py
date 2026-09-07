"""Unit tests for the minimal v1 load fixes (BUG-942 items 1, 3 and 5).

v1 is no longer maintained, so these fixes are line-level only:

* jitter on the four v1 poll sleeps -- a deterministic interval keeps every
  client launched together phase-locked for the whole run;
* a pipeline poll budget measured in minutes rather than 5h33m;
* a poll log that never interpolates the response body, lazily.

Connection reuse (item 3) is covered in ``tests/unit/utils/request_utils_test.py``.
"""

import ast
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# The four v1 poll loops named in BUG-942. ``rlm.py``'s loop is deliberately
# excluded: it lives inside a Python source *string* injected into a remote
# sandbox, where one sandbox runs one job and there is no fleet to decorrelate.
V1_POLL_LOOPS = [
    "aixplain/v1/modules/model/__init__.py",
    "aixplain/v1/modules/agent/__init__.py",
    "aixplain/v1/modules/team_agent/__init__.py",
    "aixplain/v1/modules/pipeline/asset.py",
]


def _sleep_calls(path):
    """Every ``time.sleep(...)`` call node in *path*, ignoring strings/comments."""
    tree = ast.parse((REPO_ROOT / path).read_text())
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "sleep"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "time"
    ]


class TestV1PollJitter:
    """Every v1 poll sleep must be jittered."""

    @pytest.mark.parametrize("path", V1_POLL_LOOPS)
    def test_every_poll_sleep_is_jittered(self, path):
        """AST-checked so a comment or docstring can't satisfy the assertion."""
        calls = _sleep_calls(path)

        assert calls, f"no time.sleep found in {path}"
        for call in calls:
            source = ast.dump(call)
            assert "random" in source and "uniform" in source, f"{path}:{call.lineno} sleeps without jitter"

    @pytest.mark.parametrize("path", V1_POLL_LOOPS)
    def test_random_is_imported(self, path):
        assert "\nimport random\n" in (REPO_ROOT / path).read_text()

    def test_model_sync_poll_jitters_its_sleep(self):
        """Behavioural check on one loop: the delay is not the nominal interval."""
        from aixplain.v1.modules.model import Model

        model = Model(id="m-1", name="m", api_key="k")
        polls = [
            {"completed": False, "status": "IN_PROGRESS"},
            {"completed": True, "status": "SUCCESS", "data": ""},
        ]
        delays = []

        with patch.object(Model, "poll", side_effect=polls):
            with patch("aixplain.v1.modules.model.time.sleep", side_effect=delays.append):
                model.sync_poll("https://example.com/poll", wait_time=1.0, timeout=60)

        assert len(delays) == 1
        assert delays[0] != 1.0
        assert 0.8 <= delays[0] <= 1.2

    def test_model_sync_poll_delays_differ_across_runs(self):
        """Two clients started together must not sleep in lockstep."""
        from aixplain.v1.modules.model import Model

        observed = []
        for _ in range(2):
            model = Model(id="m-1", name="m", api_key="k")
            polls = [{"completed": False, "status": "IN_PROGRESS"}] * 3 + [
                {"completed": True, "status": "SUCCESS", "data": ""}
            ]
            delays = []
            with patch.object(Model, "poll", side_effect=polls):
                with patch("aixplain.v1.modules.model.time.sleep", side_effect=delays.append):
                    model.sync_poll("https://example.com/poll", wait_time=1.0, timeout=60)
            observed.append(delays)

        assert observed[0] != observed[1]

    def test_backoff_ladder_is_preserved(self):
        """Jitter replaces the constant; the x1.1 growth must survive."""
        from aixplain.v1.modules.model import Model

        model = Model(id="m-1", name="m", api_key="k")
        polls = [{"completed": False, "status": "IN_PROGRESS"}] * 8 + [
            {"completed": True, "status": "SUCCESS", "data": ""}
        ]
        delays = []

        with patch.object(Model, "poll", side_effect=polls):
            with patch("aixplain.v1.modules.model.random.uniform", return_value=1.0):
                with patch("aixplain.v1.modules.model.time.sleep", side_effect=delays.append):
                    model.sync_poll("https://example.com/poll", wait_time=1.0, timeout=600)

        assert delays == sorted(delays)
        assert delays[-1] > delays[0]
        assert delays[1] == pytest.approx(1.1)


class TestPipelineTimeoutDefault:
    """BUG-942 item 5a: the default budget was 20,000s (5h33m)."""

    def test_run_default_timeout_is_measured_in_minutes(self):
        import inspect

        from aixplain.v1.modules.pipeline.asset import Pipeline

        default = inspect.signature(Pipeline.run).parameters["timeout"].default

        assert default == 1800.0
        assert default / 60 <= 60, "default budget should be under an hour"

    def test_polling_default_timeout_matches_run(self):
        import inspect

        from aixplain.v1.modules.pipeline.asset import Pipeline

        polling = getattr(Pipeline, "_Pipeline__polling")
        assert inspect.signature(polling).parameters["timeout"].default == 1800.0

    def test_no_twenty_thousand_second_default_remains(self):
        source = (REPO_ROOT / "aixplain/v1/modules/pipeline/asset.py").read_text()

        assert "20000.0" not in source


class TestPipelinePollLogging:
    """BUG-942 item 5b: the full response body was logged at INFO every poll."""

    @staticmethod
    def _poll(caplog, body):
        from aixplain.v1.modules.pipeline.asset import Pipeline

        pipeline = Pipeline(id="p-1", name="p", api_key="k", nodes=[])
        response = Mock()
        response.json.return_value = body

        with patch("aixplain.v1.modules.pipeline.asset._request_with_retry", return_value=response):
            with caplog.at_level(logging.DEBUG, logger="root"):
                pipeline.poll("https://example.com/poll", response_version="v1")
        return caplog.records

    def test_poll_does_not_log_the_response_body(self, caplog):
        """A 500KB transcript used to be emitted on every poll."""
        secret_body = "x" * 5000
        records = self._poll(caplog, {"status": "IN_PROGRESS", "completed": False, "transcript": secret_body})

        for record in records:
            assert secret_body not in record.getMessage()

    def test_poll_log_uses_lazy_percent_args(self, caplog):
        """Eager f-strings stringify the payload even when the level is off."""
        records = self._poll(caplog, {"status": "IN_PROGRESS", "completed": False})
        poll_records = [r for r in records if "Single Poll for Pipeline" in r.getMessage()]

        assert poll_records, records
        record = poll_records[0]
        assert "%s" in record.msg
        assert record.args == ("p-1", "pipeline_process", "https://example.com/poll", "IN_PROGRESS")

    def test_poll_log_is_no_longer_at_info(self, caplog):
        """One line per poll at INFO is noise even without the body."""
        records = self._poll(caplog, {"status": "IN_PROGRESS", "completed": False})
        poll_records = [r for r in records if "Single Poll for Pipeline" in r.getMessage()]

        assert poll_records
        assert all(r.levelno == logging.DEBUG for r in poll_records)

    def test_no_eager_body_interpolation_left_in_the_poll_path(self):
        """Guard: no f-string logging call in ``poll`` mentions ``{resp}``."""
        source = (REPO_ROOT / "aixplain/v1/modules/pipeline/asset.py").read_text()

        assert 'logging.info(f"Single Poll' not in source
        assert "): {resp}" not in source
