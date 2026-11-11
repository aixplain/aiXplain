"""Repository-only hardening that ships outside the wheel (BUG-1452).

* The shipped ``marketplace-search`` skill must not splice the API key (or
  marketplace values) into a shell command.
* The eval dashboard binds to loopback by default.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _shell_blocks(markdown: str):
    return re.findall(r"```(?:bash|sh|shell)\n(.*?)```", markdown, flags=re.S)


def test_skills_never_expand_the_api_key_into_a_command():
    for skill in sorted((REPO_ROOT / "skills").glob("*/SKILL.md")):
        for block in _shell_blocks(skill.read_text(encoding="utf-8")):
            assert "$AIXPLAIN_API_KEY" not in block, skill
            assert "${AIXPLAIN_API_KEY" not in block, skill
            assert "$TEAM_API_KEY" not in block, skill
            assert not re.search(r"python3?\s+-c\s+'", block), skill


def test_marketplace_search_snippet_uses_quoted_heredocs_and_the_environment_key():
    text = (REPO_ROOT / "skills" / "marketplace-search" / "SKILL.md").read_text(encoding="utf-8")
    block = next(b for b in _shell_blocks(text) if "Aixplain(" in b)
    assert "python3 - " in block and "<<'PY'" in block
    assert "<<'JSON'" in block
    assert "Aixplain()" in block
    assert "json.load" in block


def test_eval_dashboard_binds_to_loopback_by_default():
    config = (REPO_ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[server\]\s*$(.*?)(?=^\[|\Z)", config, flags=re.M | re.S)
    assert section, "missing [server] section"
    address = re.search(r'^\s*address\s*=\s*"([^"]*)"', section.group(1), flags=re.M)
    assert address and address.group(1) == "127.0.0.1"


def test_eval_dashboard_documents_the_loopback_flag():
    source = (REPO_ROOT / "eval_dashboard" / "app.py").read_text(encoding="utf-8")
    assert "--server.address 127.0.0.1" in source
