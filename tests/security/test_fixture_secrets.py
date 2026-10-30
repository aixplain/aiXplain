"""Committed recordings carry no credentials (ENG-3782, layer 5).

The contract and stream-replay layers commit recorded platform responses and
SSE bodies. pre-commit.yaml's gitleaks scan covers the tree, but its rules
want a credential name on the same line as a 64-hex key; a recording can hold
one as a bare JSON value. This scans every recording for credential-shaped
values, wherever they sit.

Only counts and file names are reported, never a matched value.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest

TESTS = Path(__file__).resolve().parents[1]
RECORDINGS = sorted(
    [*(TESTS / "contract" / "recordings").rglob("*.json"), *(TESTS / "stream_replay" / "streams").rglob("*.json")]
)

SECRET_VALUE_PATTERNS = (
    re.compile(r"\b[0-9a-f]{64}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
)


def _hits(path: Path) -> List[str]:
    text = path.read_text(encoding="utf-8")
    return [p.pattern[:20] for p in SECRET_VALUE_PATTERNS if p.search(text)]


@pytest.mark.parametrize("path", RECORDINGS, ids=[p.relative_to(TESTS).as_posix() for p in RECORDINGS])
def test_recording_carries_no_credential(path: Path) -> None:
    assert _hits(path) == []


def test_recordings_were_found() -> None:
    assert len(RECORDINGS) > 30


def test_the_scan_sees_a_bare_platform_key() -> None:
    sample = '{"response": {"json": {"value": "%s"}}}' % ("ab12" * 16)
    assert any(p.search(sample) for p in SECRET_VALUE_PATTERNS)
