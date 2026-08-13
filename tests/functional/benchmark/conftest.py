import os

import pytest

# These tests hit the live backend, so they are skipped when no credential is
# available -- the pattern in tests/functional/v2/conftest.py.
#
# This directory has no CI leg: 04dea96e dropped it, and it stays parked until
# proven green against the test backend (ENG-3544, PARKED_TARGETS in
# tests/unit/test_ci_matrix_coverage.py). The guard is here anyway so that a
# manual `pytest tests/functional/benchmark` without a key skips cleanly instead
# of failing on unauthenticated 403s, which is how the rest of
# tests/functional behaves.
#
# It is deliberately NOT an unconditional skip. A directory-wide
# `pytest_collection_modifyitems` skip is what made the `agent` and `team_agent`
# legs report green while executing nothing (ENG-3544). If an individual test is
# failing, skip or xfail *that test* with a ticket in the reason -- never the
# directory.


@pytest.fixture(autouse=True)
def _require_api_key():
    """Skip a benchmark functional test when there is no API key to run it with.

    Function-scoped rather than session-scoped so the skip is raised freshly per
    test instead of relying on cached-fixture-exception behaviour, and applied at
    setup time rather than at collection so `--collect-only` still reports the
    true inventory.
    """
    if not (os.getenv("TEAM_API_KEY") or os.getenv("AIXPLAIN_API_KEY")):
        pytest.skip("TEAM_API_KEY or AIXPLAIN_API_KEY environment variable is required for functional tests")
