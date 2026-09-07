"""Shared cleanup fixture for the functional suite (BUG-947).

`resource_tracker` used to be copy-pasted into four test modules, two of which
defined it twice, and every copy ended its teardown with ``except Exception:
pass``. Fixing that meant editing six identical bodies, which is exactly how one
gets missed -- so the fixture now lives here, once, and
`tests/unit/test_functional_hygiene.py` fails if a local copy reappears.

The logic is in `tests/cleanup_guards.py` so it can be unit-tested without a
backend; this module only wires it into pytest.
"""

import pytest

from tests.cleanup_guards import ResourceTracker, finish_cleanup


@pytest.fixture
def resource_tracker(request):
    """Tracks resources created during a test for guaranteed cleanup.

    Append anything exposing ``delete()`` right after you create it, or use
    ``add_callback(label, fn)`` for a factory that returns a dict instead of a
    deletable object. Teardown runs whether the test passes, fails or errors --
    and once per `flaky` rerun -- so an assertion failure above cannot leak the
    resource.

    Teardown deletes newest-first, treats a resource the test already deleted as
    a success, and fails the test if anything is left behind. Set
    ``AIXPLAIN_FUNCTIONAL_CLEANUP_STRICT=0`` to downgrade that to a warning.

    Deliberately not autouse and it never skips: an autouse fixture that could
    call ``pytest.skip()`` is the shape `tests/unit/test_ci_matrix_coverage.py`
    flags as a directory-wide blanket skip (ENG-3544).
    """
    tracker = ResourceTracker()
    yield tracker
    finish_cleanup(tracker, request.node.nodeid)
