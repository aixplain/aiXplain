"""aiXplain SDK Library.

aiXplain SDK enables python programmers to add AI functions
to their software.

Copyright 2022 The aiXplain SDK authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import logging
from dotenv import load_dotenv


def _load_cwd_dotenv() -> bool:
    """Load only the ``.env`` in the current working directory, never an ancestor's.

    A bare ``load_dotenv()`` -- and ``find_dotenv(usecwd=True)`` -- searches
    *parent* directories, so a ``.env`` shipped inside a cloned sample project or
    a bug-report attachment could set ``BACKEND_URL``, ``TEAM_API_KEY``,
    ``LOG_LEVEL`` or ``SENTRY_DSN`` for a user who merely ``cd``s into a
    subdirectory and runs their own script with their own key (BUG-939). Loading
    an explicit path removes the walk-up while keeping the documented behaviour
    for a ``.env`` in the working directory itself.

    Existing environment variables still win (``override=False``), as with the
    bare call this replaces.

    Returns:
        bool: True when a ``.env`` was found in the working directory and loaded.
    """
    return load_dotenv(os.path.join(os.getcwd(), ".env"), override=False)


_load_cwd_dotenv()

from aixplain._compat import install as _install_compat  # noqa: E402

_install_compat()

# The whole v2 surface is re-exported here, so nothing a caller needs carries a
# version segment in its import path: ``from aixplain import Budget, Privacy,
# APIKeyLimits`` rather than ``from aixplain.v2 import ...``. ``aixplain.v2``
# already collected these names -- one level too deep for a caller who only ever
# writes ``from aixplain import ...``.
#
# A star import rather than a copied list of ~130 names: it cannot drift from
# ``aixplain.v2.__all__``, and IDEs and type checkers resolve it through that
# same ``__all__``, so autocomplete still works. ``tests/unit/v2/
# test_plain_data_inputs.py`` asserts the two stay in step.
#
# This costs no import time: ``from .v2.core import ...`` already executes
# ``aixplain/v2/__init__.py`` as the parent package.
from .v2 import *  # noqa: F403,E402
from .v2 import __all__ as _V2_ALL  # noqa: E402
from .v2.core import Aixplain  # noqa: E402,F401
from .v2.file import File  # noqa: E402,F401

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)


_AIXPLAIN_V2_DEPRECATION = (
    "'aixplain.aixplain_v2' is deprecated and will be removed in a future release. "
    "Construct a client explicitly instead: 'from aixplain import Aixplain; aix = Aixplain()'."
)


def __getattr__(name: str):
    """Lazily construct the deprecated module-level ``aixplain_v2`` client.

    Constructing it at import time and swallowing the failure left a public
    symbol bound to ``None``, so a missing credential surfaced much later as
    ``AttributeError: 'NoneType' object has no attribute 'Agent'`` instead of the
    actionable message ``Aixplain()`` already raises (BUG-946). Deferring the
    construction to first access keeps ``import aixplain`` working without a key
    -- which ``aixplain --help`` and unit-test collection rely on -- while
    letting the real error reach whoever actually asks for the client.

    Args:
        name (str): Attribute being looked up on the package.

    Returns:
        Aixplain: The lazily constructed client, cached in module globals.

    Raises:
        AttributeError: If ``name`` is anything other than ``aixplain_v2``.
    """
    if name != "aixplain_v2":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    import warnings

    warnings.warn(_AIXPLAIN_V2_DEPRECATION, DeprecationWarning, stacklevel=2)
    # Raises the real error (e.g. "API key is required...") when unconfigured.
    client = Aixplain()
    # Cache so repeated access returns the same client and skips this hook.
    globals()["aixplain_v2"] = client
    return client


def __dir__():
    """Keep the lazily provided ``aixplain_v2`` discoverable via ``dir()``."""
    return sorted(set(globals()) | {"aixplain_v2"})


# ``aixplain_v2`` is deliberately absent: it stays importable by name through
# ``__getattr__`` above, but keeping it here would make ``from aixplain import *``
# construct a client -- and therefore raise -- in a keyless environment.
__all__ = list(_V2_ALL)
