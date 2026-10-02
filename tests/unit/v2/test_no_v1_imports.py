"""Guard test: ensure no removed-v1 import path leaks into the v2 package.

v1 is gone (PROD-2918), so ``from aixplain.enums import ...`` inside ``aixplain/v2/``
would now raise at import time rather than merely dragging in the old env-var
validation chain. The rule is unchanged; only the consequence got worse.
"""

import ast
import os
import re
from pathlib import Path

import pytest

V2_PACKAGE_DIR = Path(__file__).resolve().parents[3] / "aixplain" / "v2"

# No file is exempt. ``enums_include.py`` (the generated v1 enum shim) and
# ``core.py``'s guarded sync into ``aixplain.utils.config`` both went with v1.
EXCLUDED_FILES = set()

# Modules under ``aixplain.utils`` that v2 *may* import. ``url_safety`` is the
# shared URL trust policy (BUG-939) and imports nothing from ``aixplain`` at all,
# so it cannot pull a chain of anything in; ``test_url_safety_stays_self_contained``
# below keeps that true. ``user_info_utils`` builds the agent run ``metaData``
# object and likewise imports nothing from the package.
ALLOWED_SHARED_MODULES = {"aixplain.utils.url_safety", "aixplain.utils.user_info_utils"}

# Patterns that constitute a v1 import.
# Matches:  from aixplain.modules  / from aixplain.factories
#           from aixplain.enums    / from aixplain.utils
#           import aixplain.modules  (etc.)
V1_IMPORT_PATTERNS = re.compile(
    r"from\s+aixplain\.(modules|factories|enums|utils)"
    r"|import\s+aixplain\.(modules|factories|enums|utils)"
)


def _collect_v2_python_files():
    """Yield (relative_name, full_path) for every .py file in aixplain/v2/."""
    for root, _dirs, files in os.walk(V2_PACKAGE_DIR):
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            if name in EXCLUDED_FILES:
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, V2_PACKAGE_DIR)
            yield rel, full


def _find_v1_imports_via_ast(filepath):
    """Use AST to find v1 imports, ignoring comments and strings."""
    with open(filepath, "r") as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module in ALLOWED_SHARED_MODULES:
                continue
            parts = node.module.split(".")
            # e.g. from aixplain.modules.model.utils import ...
            if (
                len(parts) >= 2
                and parts[0] == "aixplain"
                and parts[1]
                in (
                    "modules",
                    "factories",
                    "enums",
                    "utils",
                )
            ):
                names = ", ".join(alias.name for alias in node.names)
                violations.append(f"  line {node.lineno}: from {node.module} import {names}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ALLOWED_SHARED_MODULES:
                    continue
                parts = alias.name.split(".")
                if (
                    len(parts) >= 2
                    and parts[0] == "aixplain"
                    and parts[1]
                    in (
                        "modules",
                        "factories",
                        "enums",
                        "utils",
                    )
                ):
                    violations.append(f"  line {node.lineno}: import {alias.name}")
    return violations


_v2_files = list(_collect_v2_python_files())


@pytest.mark.parametrize("rel_name,filepath", _v2_files, ids=[r for r, _ in _v2_files])
def test_no_v1_imports(rel_name, filepath):
    """``aixplain/v2/{rel_name}`` must not import from v1 modules."""
    violations = _find_v1_imports_via_ast(filepath)
    assert not violations, f"v1 imports found in aixplain/v2/{rel_name}:\n" + "\n".join(violations)


@pytest.mark.parametrize("module", sorted(ALLOWED_SHARED_MODULES))
def test_url_safety_stays_self_contained(module):
    """Each exempted shared module must not reach back into the package.

    They are exempted from the rule above only because they import nothing from
    ``aixplain``; if that ever changes, the exemption would silently reopen an
    import chain for every v2 module that uses them.
    """
    path = V2_PACKAGE_DIR.parent.joinpath(*module.split(".")[1:]).with_suffix(".py")
    tree = ast.parse(path.read_text(), filename=str(path))

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    assert not [name for name in imported if name.split(".")[0] == "aixplain"]
