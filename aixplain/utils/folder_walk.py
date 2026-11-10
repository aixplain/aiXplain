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
* symlinked directories (and Windows junctions) are never descended into;
* ``include`` re-admits paths the dot/cache rule would skip, but never a
  symlink that escapes the root. Naming a file inside a hidden folder
  (``.git/HEAD``) admits only that file, not the rest of the folder; naming
  the folder itself (``.well-known``) admits all of it.

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


def _is_hidden_path(rel_path: str) -> bool:
    """True if any component of *rel_path* is a dot-name or an excluded cache directory."""
    parts = rel_path.split("/")
    return any(part.startswith(".") for part in parts) or any(part in DEFAULT_EXCLUDED_DIRS for part in parts[:-1])


def _admitted_whole(rel_dir: str, patterns: Sequence[str]) -> bool:
    """True if *rel_dir* is not inside a hidden/cache folder, or an include pattern names such a folder whole.

    ``include=[".git/HEAD"]`` keeps ``.git/`` walkable so ``HEAD`` can be found,
    but must not admit ``.git/config``: inside a hidden folder that is admitted
    only by a deeper pattern, each file has to match a pattern itself.
    """
    if not rel_dir:
        return True
    parts = rel_dir.split("/")
    hidden_from = next(
        (i for i, part in enumerate(parts) if part.startswith(".") or part in DEFAULT_EXCLUDED_DIRS),
        None,
    )
    if hidden_from is None:
        return True
    return any(_matches("/".join(parts[: i + 1]), patterns) for i in range(hidden_from, len(parts)))


def _is_redirected_dir(path: str, parent_real: str) -> bool:
    """True if directory *path* is a symlink, a Windows junction or otherwise resolves elsewhere.

    ``os.path.islink`` is ``False`` for a junction, and ``os.walk`` enters it,
    so compare the resolved path with where the directory claims to live.
    """
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is not None and isjunction(path):
        return True
    expected = os.path.join(parent_real, os.path.basename(path))
    return os.path.normcase(os.path.realpath(path)) != os.path.normcase(expected)


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

        dir_real = os.path.realpath(dirpath)
        whole = _admitted_whole(rel_dir, patterns)
        kept_dirs: List[str] = []
        for name in sorted(dirnames):
            rel_path = _rel_join(rel_dir, name)
            if _is_redirected_dir(os.path.join(dirpath, name), dir_real):
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
                # A link to a hidden/cache path inside the root (``notes.md ->
                # .env``) must not smuggle out what the dot/cache rule skips.
                rel_target = os.path.relpath(target, root_real).replace(os.sep, "/")
                if _is_hidden_path(rel_target) and not _matches(rel_target, patterns):
                    skipped.append(rel_path + " (symlink to a hidden path)")
                    continue
            if (name.startswith(".") or not whole) and not _matches(rel_path, patterns):
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
