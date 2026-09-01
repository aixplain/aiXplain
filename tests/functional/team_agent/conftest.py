import os

import pytest

# These tests hit the live backend, so they are skipped when no credential is
# available -- the pattern in tests/functional/v2/conftest.py.
#
# They are deliberately NOT skipped unconditionally. A directory-wide
# `pytest_collection_modifyitems` skip made the `team_agent` CI leg collect 15
# tests, execute 0, and report green (ENG-3544). If an individual test is
# failing, skip or xfail *that test* with a ticket in the reason -- never the
# directory.


@pytest.fixture(autouse=True)
def _require_api_key():
    """Skip a team-agent functional test when there is no API key to run it with.

    Function-scoped rather than session-scoped so the skip is raised freshly per
    test instead of relying on cached-fixture-exception behaviour, and applied at
    setup time rather than at collection so `--collect-only` still reports the
    true inventory.
    """
    if not (os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")):
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")
