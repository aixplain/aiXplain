"""``import aixplain`` must not pull in pandas/numpy (BUG-949).

pandas alone was ~240-450 ms and tens of MB of RSS on every process start,
reached via ``aixplain.v2.core -> agent_evaluator``, even for callers that never
evaluate anything.
"""

import os
import subprocess
import sys

from aixplain.v2._lazy import _LazyModule


def _run(code: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.setdefault("TEAM_API_KEY", "dummy-key-for-import-test")
    return subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)


def test_import_aixplain_does_not_import_pandas():
    result = _run("import aixplain, sys; assert 'pandas' not in sys.modules, 'pandas imported'")
    assert result.returncode == 0, result.stderr


def test_import_aixplain_does_not_import_numpy():
    result = _run("import aixplain, sys; assert 'numpy' not in sys.modules, 'numpy imported'")
    assert result.returncode == 0, result.stderr


def test_eval_modules_still_load_pandas_on_use():
    code = (
        "import sys\n"
        "from aixplain.v2 import eval_results_display as m\n"
        "assert 'pandas' not in sys.modules\n"
        "df = m.pd.DataFrame({'a': [1]})\n"
        "assert 'pandas' in sys.modules and len(df) == 1\n"
    )
    result = _run(code)
    assert result.returncode == 0, result.stderr


class TestLazyModule:
    def test_loads_on_first_attribute_and_caches(self):
        proxy = _LazyModule("json")
        assert object.__getattribute__(proxy, "_mod") is None
        assert proxy.dumps({"a": 1}) == '{"a": 1}'
        loaded = object.__getattribute__(proxy, "_mod")
        assert loaded is sys.modules["json"]
        proxy.loads("1")
        assert object.__getattribute__(proxy, "_mod") is loaded

    def test_repr_does_not_import(self):
        proxy = _LazyModule("some_module_that_does_not_exist_949")
        assert "some_module_that_does_not_exist_949" in repr(proxy)
