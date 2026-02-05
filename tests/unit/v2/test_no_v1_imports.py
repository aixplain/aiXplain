"""Guard test: ensure no v1 imports leak into the v2 package.

The v2 SDK must be fully self-contained so that users who only use
``Aixplain(api_key=...)`` never trigger the v1 env-var validation
chain (aixplain.modules -> utils/config -> validate_api_keys).
"""

import ast
import os
import re
from pathlib import Path

import pytest

V2_PACKAGE_DIR = Path(__file__).resolve().parents[3] / "aixplain" / "v2"

# Auto-generated compatibility shim — allowed to import v1
EXCLUDED_FILES = {"enums_include.py"}

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
