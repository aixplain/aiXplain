"""Safe directory walk for folder uploads (BUG-1452).

``Skill.save`` / ``Skill.update`` on a folder and ``File.save`` on a directory
publish every file they walk. A bare ``os.walk`` lists symlinked files under
``filenames`` (and ``open`` follows them), and skips nothing, so a ``.env``, a
``.git/config`` or a link pointing at a file outside the folder would be
uploaded along with the bundle.

:func:`walk_upload_tree` is the one walk all three call sites share:

* dot-files and dot-directories (``.env``, ``.git/``, ``.venv/``,
  ``.DS_Store``, ...) and well-known cache directories
  (:data:`DEFAULT_EXCLUDED_DIRS`) are skipped by default;
* a symlinked file is kept only when its real path stays inside the root;
* symlinked directories are never descended into;
* ``include`` re-admits paths the dot/cache rule would skip, but never a
  symlink that escapes the root.

Skipped entries are reported once, as a single WARNING listing their relative
paths (never their contents). Like :mod:`aixplain.utils.url_safety`, this module
imports nothing from ``aixplain.v2``.
"""

import fnmatch
import logging
import os
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

#: Directory names skipped by default in addition to every dot-directory.
DEFAULT_EXCLUDED_DIRS = frozenset({"__pycache__", "node_modules"})


def _rel_join(rel_dir: str, name: str) -> str:
    return f"{rel_dir}/{name}" if rel_dir else name


def _matches(rel_path: str, patterns: Sequence[str]) -> bool:
    """True if *rel_path* (POSIX, relative to the root) matches an include pattern."""
    return any(rel_path == pattern or fnmatch.fnmatchcase(rel_path, pattern) for pattern in patterns)


def _dir_is_included(rel_path: str, patterns: Sequence[str]) -> bool:
    """True if an include pattern names *rel_path* or anything beneath it."""
    prefix = rel_path + "/"
    return _matches(rel_path, patterns) or any(pattern.startswith(prefix) for pattern in patterns)


def _is_within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:  # different drives on Windows
        return False


def walk_upload_tree(
    root: str,
    *,
    include: Optional[Iterable[str]] = None,
) -> Iterator[Tuple[str, List[str], List[str]]]:
    """Walk *root* like ``os.walk`` but yield only entries that are safe to upload.

    Args:
        root: The local folder being uploaded.
        include: Optional relative POSIX paths or ``fnmatch`` patterns (relative
            to *root*, e.g. ``".well-known/*"`` or ``".env.example"``) that are
            uploaded even though the default dot/cache rule would skip them.
            Never re-admits a symlink that resolves outside *root*.

    Yields:
        ``(dirpath, dirnames, filenames)``, as ``os.walk`` does, with both lists
        sorted and already filtered. ``dirnames`` is the list ``os.walk``
        recurses into, so a caller may prune it further in place.
    """
    patterns = tuple(p.strip().strip("/") for p in (include or ()) if p and p.strip().strip("/"))
    root_real = os.path.realpath(root)
    skipped: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root)
        rel_dir = "" if rel_dir == "." else rel_dir.replace(os.sep, "/")

        kept_dirs: List[str] = []
        for name in sorted(dirnames):
            rel_path = _rel_join(rel_dir, name)
            if os.path.islink(os.path.join(dirpath, name)):
                skipped.append(rel_path + "/ (symlinked directory)")
                continue
            if (name.startswith(".") or name in DEFAULT_EXCLUDED_DIRS) and not _dir_is_included(rel_path, patterns):
                skipped.append(rel_path + "/")
                continue
            kept_dirs.append(name)
        dirnames[:] = kept_dirs

        kept_files: List[str] = []
        for name in sorted(filenames):
            rel_path = _rel_join(rel_dir, name)
            full_path = os.path.join(dirpath, name)
            if os.path.islink(full_path):
                target = os.path.realpath(full_path)
                if not _is_within(target, root_real) or not os.path.isfile(target):
                    skipped.append(rel_path + " (symlink outside the folder)")
                    continue
            if name.startswith(".") and not _matches(rel_path, patterns):
                skipped.append(rel_path)
                continue
            kept_files.append(name)

        yield dirpath, dirnames, kept_files

    if skipped:
        logger.warning(
            "Skipped %d path(s) while uploading %s (hidden files, VCS/cache folders and symlinks leaving the "
            "folder are not uploaded; pass include=[...] to add hidden paths deliberately): %s",
            len(skipped),
            root,
            ", ".join(skipped),
        )
