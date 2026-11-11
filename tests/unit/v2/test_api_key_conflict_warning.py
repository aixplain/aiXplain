"""``Aixplain()`` warns when ``TEAM_API_KEY`` and ``AIXPLAIN_API_KEY`` disagree.

The check used to live in ``aixplain/utils/config.py``, which nothing imported
after the v1 removal, so it never ran (BUG-1456). It now lives where the key is
actually resolved. It warns rather than raises: the old raise never fired on
0.3.0, so turning a working setup into a hard failure would be a breaking change.
"""

import os
import warnings
from unittest.mock import patch

import pytest

from aixplain.v2.core import Aixplain

TEAM = "team-key-value-1234"
AIX = "aixplain-key-value-5678"


def _conflict_warnings(caught):
    return [w for w in caught if issubclass(w.category, UserWarning) and "AIXPLAIN_API_KEY" in str(w.message)]


def _construct(env, **kwargs):
    with patch.dict(os.environ, env, clear=False):
        for name in ("TEAM_API_KEY", "AIXPLAIN_API_KEY"):
            if name not in env:
                os.environ.pop(name, None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client = Aixplain(**kwargs)
    return client, caught


def test_differing_env_keys_warn_and_use_team_key():
    client, caught = _construct({"TEAM_API_KEY": TEAM, "AIXPLAIN_API_KEY": AIX})

    found = _conflict_warnings(caught)
    assert len(found) == 1
    message = str(found[0].message)
    assert "TEAM_API_KEY" in message
    assert TEAM not in message and AIX not in message, "the warning must never echo key material"
    assert client.api_key == TEAM


@pytest.mark.parametrize(
    "env",
    [
        {"TEAM_API_KEY": TEAM, "AIXPLAIN_API_KEY": TEAM},
        {"TEAM_API_KEY": TEAM},
        {"AIXPLAIN_API_KEY": AIX},
    ],
    ids=["equal", "team-only", "aixplain-only"],
)
def test_consistent_env_keys_do_not_warn(env):
    client, caught = _construct(env)

    assert _conflict_warnings(caught) == []
    assert client.api_key == next(iter(env.values()))


def test_explicit_api_key_skips_the_check():
    client, caught = _construct({"TEAM_API_KEY": TEAM, "AIXPLAIN_API_KEY": AIX}, api_key="explicit-key")

    assert _conflict_warnings(caught) == []
    assert client.api_key == "explicit-key"
