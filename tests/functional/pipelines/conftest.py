import os

import pytest

# These tests hit the live backend, so they are skipped when no credential is
# available -- the pattern in tests/functional/v2/conftest.py.
#
# `run_test.py` is executed by the `pipeline_2.0_v1` leg, which always has a
# credential, so this changes nothing there. `designer_test.py` and
# `create_test.py` have no leg: 04dea96e dropped theirs and they stay parked
# until proven green against the test backend (ENG-3544, PARKED_TARGETS in
# tests/unit/test_ci_matrix_coverage.py). The guard means a manual run of either
# without a key skips cleanly instead of failing on unauthenticated 403s.
#
# It is deliberately NOT an unconditional skip. A directory-wide
# `pytest_collection_modifyitems` skip is what made the `agent` and `team_agent`
# legs report green while executing nothing (ENG-3544). If an individual test is
# failing, skip or xfail *that test* with a ticket in the reason -- never the
# directory.


@pytest.fixture(autouse=True)
def _require_api_key():
    """Skip a pipeline functional test when there is no API key to run it with.

    Function-scoped rather than session-scoped so the skip is raised freshly per
    test instead of relying on cached-fixture-exception behaviour, and applied at
    setup time rather than at collection so `--collect-only` still reports the
    true inventory.
    """
    if not (os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")):
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")
