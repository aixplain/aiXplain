"""Regression tests for Utility.run.

`Utility.run` was declared as a ``@classmethod`` overriding the instance method
``RunnableResourceMixin.run``. Inside a classmethod ``super()`` binds to the class, so the
descriptor yields the *unbound* function and ``self`` is never supplied — every call raised
``TypeError: run() missing 1 required positional argument: 'self'``.

The bug was invisible because no test exercised ``Utility.run``.
"""

from unittest.mock import patch

from aixplain.v2.resource import RunnableResourceMixin
from aixplain.v2.utility import Utility


def test_run_is_an_instance_method_not_a_classmethod():
    """A classmethod here breaks `super().run()`; guard the shape directly."""
    assert not isinstance(Utility.__dict__["run"], classmethod), (
        "Utility.run must be an instance method so super().run() binds self"
    )


def test_run_delegates_to_the_mixin_with_self():
    """The regression: calling run() on an instance must reach the mixin bound."""
    utility = Utility(id="6789")

    # autospec=True keeps the descriptor protocol, so the mock receives `self` exactly as
    # the real method would. A plain Mock would not bind and could never tell the two
    # states apart.
    with patch.object(RunnableResourceMixin, "run", autospec=True, return_value="ran") as mocked_run:
        result = utility.run(data="hello")

    assert result == "ran"
    mocked_run.assert_called_once()
    # `self` must be the instance we called it on — this is what the classmethod broke.
    assert mocked_run.call_args.args[0] is utility
    assert mocked_run.call_args.kwargs == {"data": "hello"}
