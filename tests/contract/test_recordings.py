"""Hygiene of the contract recordings (ENG-3782, layer 1).

A recording is only useful if it is scrubbed, says where it came from, and is
replayed by some test.
"""

import json
import re
from pathlib import Path

import pytest

from tests.support.platform_replay import RECORDINGS_DIR

NAMES = sorted(p.relative_to(RECORDINGS_DIR).with_suffix("").as_posix() for p in RECORDINGS_DIR.rglob("*.json"))
TEST_SOURCES = "\n".join(p.read_text(encoding="utf-8") for p in Path(__file__).parent.glob("test_*.py"))
SECRETS = (
    re.compile(r"\b[0-9a-f]{64}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
)


@pytest.mark.parametrize("name", NAMES)
def test_recording_is_scrubbed_and_says_where_it_came_from(name: str) -> None:
    data = json.loads((RECORDINGS_DIR / (name + ".json")).read_text(encoding="utf-8"))
    provenance = data["provenance"]
    assert provenance["source"] in {"live", "reconstructed", "generated"}
    if provenance["source"] != "live":
        assert provenance["derived_from"], "a non-live recording must name the code its shape came from"
    text = json.dumps(data["response"])
    assert [p.pattern for p in SECRETS if p.search(text)] == []


@pytest.mark.parametrize("name", NAMES)
def test_recording_is_replayed_by_a_test(name: str) -> None:
    assert '"%s"' % name in TEST_SOURCES
