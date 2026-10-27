#!/usr/bin/env python3
"""Back-test the ENG-3782 test layers against the fixes they are meant to catch.

ENG-3782's acceptance criteria ask, for each P1 layer, that at least three
catalogued fixes from ENG-3761 be re-introduced and the layer fail on each.
This script does that reproducibly: each entry in ``LAYERS`` is a fix's source
change undone as an exact text replacement (it must match exactly the stated
number of times, so a refactor that moves the code makes the entry fail loudly
instead of silently testing nothing). For every requested fix it checks HEAD
out into a scratch worktree, applies the mutation, runs the layer's tests
there, and records which tests failed. ``baseline`` applies nothing and must
pass, which proves a failure comes from the mutation.

Usage::

    python .github/tools/backtest_layers.py --layer contract
    python .github/tools/backtest_layers.py --layer fault --fix BUG-1090 --json out.json
    python .github/tools/backtest_layers.py --all --markdown backtest.md

The worktree's source is put first on ``PYTHONPATH`` so an installed or
editable copy of the checkout cannot shadow the mutated code. Python
3.9-safe, like the rest of the SDK.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Mutation:
    path: str
    old: str
    new: str
    count: int = 1


AGENT = "aixplain/v2/agent.py"
CLIENT = "aixplain/v2/client.py"
MODEL = "aixplain/v2/model.py"
RESOURCE = "aixplain/v2/resource.py"

_SEND = "        response = self.session.request(method=method, url=url, **kwargs)"

# layer -> (pytest target, extra pytest args, {fix: [mutations]})
LAYERS: Dict[str, Tuple[str, List[str], Dict[str, List[Mutation]]]] = {
    "contract": (
        "tests/contract",
        [],
        {
            "#983": [
                Mutation(
                    AGENT,
                    "            self.diagnostic_error_codes = self._codes_from_data()",
                    "            pass  # BACKTEST #983",
                )
            ],
            "#1032": [
                Mutation(
                    CLIENT,
                    '                    error_obj.get("supplierError")\n'
                    '                    or error_obj.get("supplier_error")\n'
                    '                    or error_obj.get("message")',
                    '                    error_obj.get("message")  # BACKTEST #1032',
                )
            ],
            "#1146": [
                Mutation(
                    MODEL,
                    "        if sort_by is not None or sort_order is not None:\n            # Either half",
                    "        if False:  # BACKTEST #1146\n            # Either half",
                )
            ],
            "#1142": [Mutation(AGENT, "        self._hydrate_files()\n", "        pass  # BACKTEST #1142\n")],
        },
    ),
    "stream": (
        "tests/stream_replay",
        [],
        {
            "#987": [
                Mutation(
                    MODEL,
                    '                    delta.get("reasoning_content") if isinstance(delta.get("reasoning_content"), str) else None,',
                    "                    None,  # BACKTEST #987",
                )
            ],
            "#1012": [
                Mutation(
                    MODEL,
                    '                    delta.get("reasoning") if isinstance(delta.get("reasoning"), str) else None,\n'
                    "                    raw_details if isinstance(raw_details, list) else None,",
                    "                    None,  # BACKTEST #1012\n                    None,",
                )
            ],
            "BUG-1094": [
                Mutation(
                    MODEL,
                    "            error_message = _extract_stream_error(data)\n            if error_message is not None:",
                    "            error_message = None  # BACKTEST BUG-1094\n            if error_message is not None:",
                )
            ],
        },
    ),
    "fault": (
        "tests/fault",
        # Reverted code hangs by design here; one hung test must fail alone.
        ["--timeout", "150", "-o", "timeout_method=signal"],
        {
            "#1014": [
                Mutation(
                    CLIENT,
                    '        kwargs.setdefault("timeout", self.timeout)',
                    "        pass  # BACKTEST #1014",
                    count=2,
                )
            ],
            "BUG-1090": [
                Mutation(
                    CLIENT,
                    'RETRY_ALLOWED_METHODS = frozenset({"GET"})',
                    'RETRY_ALLOWED_METHODS = frozenset({"GET", "POST"})  # BACKTEST BUG-1090',
                )
            ],
            "BUG-942": [
                Mutation(
                    CLIENT,
                    '        "respect_retry_after_header": True,',
                    '        "respect_retry_after_header": False,  # BACKTEST BUG-942',
                )
            ],
            "BUG-1097": [
                Mutation(
                    RESOURCE,
                    "                    result = self.poll(poll_url, timeout=remaining)",
                    "                    result = self.poll(poll_url)  # BACKTEST BUG-1097",
                )
            ],
        },
    ),
    "security": (
        "tests/security",
        [],
        {
            "#1040-redirect": [
                Mutation(
                    CLIENT,
                    '        if normalize_origin(prepared_request.url or "") not in self.trusted_origins:',
                    "        if False:  # BACKTEST #1040",
                )
            ],
            "#1040-poll-url": [
                Mutation(
                    CLIENT,
                    "        if not self.is_trusted_url(url):\n            allowed",
                    "        if False:  # BACKTEST #1040\n            allowed",
                )
            ],
            "BUG-939": [
                Mutation(
                    CLIENT,
                    "        _log_request(method, url, kwargs)\n" + _SEND,
                    '        logger.debug(f"Requesting {method} {url} with kwargs: {kwargs}")  # BACKTEST BUG-939\n'
                    + _SEND,
                    count=2,
                )
            ],
            "BUG-936": [
                Mutation(
                    "aixplain/v2/rlm.py",
                    "        return any(secret in text for secret in self._secret_values())",
                    "        return False  # BACKTEST BUG-936",
                )
            ],
        },
    ),
}


def _git(*args: str) -> None:
    subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True)


def run_one(layer: str, fix: str, python: str) -> Dict[str, object]:
    target, extra, mutations = LAYERS[layer]
    scratch = Path(tempfile.mkdtemp(prefix="backtest-"))
    tree = scratch / "tree"
    _git("worktree", "add", "--detach", "-q", str(tree), "HEAD")
    try:
        for mutation in [] if fix == "baseline" else mutations[fix]:
            path = tree / mutation.path
            text = path.read_text(encoding="utf-8")
            found = text.count(mutation.old)
            if found != mutation.count:
                return {"error": "%s: expected %d match(es), found %d" % (mutation.path, mutation.count, found)}
            path.write_text(text.replace(mutation.old, mutation.new), encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": str(tree)}
        proc = subprocess.run(
            [
                python,
                "-m",
                "pytest",
                target,
                "-q",
                "-p",
                "no:cacheprovider",
                "-W",
                "ignore::DeprecationWarning",
                *extra,
            ],
            cwd=tree,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        failed = sorted(set(re.findall(r"^FAILED (\S+)", proc.stdout, re.M)))
        totals = re.findall(r"^=+ (.*) in [\d.]+s", proc.stdout, re.M)
        return {"exit": proc.returncode, "failed": failed, "totals": totals[-1] if totals else ""}
    finally:
        subprocess.run(["git", "-C", str(REPO), "worktree", "remove", "--force", str(tree)], check=False)
        shutil.rmtree(scratch, ignore_errors=True)


def render(results: Dict[str, Dict[str, Dict[str, object]]]) -> str:
    lines = ["| layer | re-introduced fix | layer result | tests that failed |", "|---|---|---|---|"]
    for layer, fixes in results.items():
        for fix, outcome in fixes.items():
            if "error" in outcome:
                verdict, failed = "mutation did not apply: %s" % outcome["error"], ""
            elif fix == "baseline":
                verdict = "green (baseline)" if outcome["exit"] == 0 else "RED BASELINE"
                failed = ""
            else:
                verdict = "caught" if outcome["exit"] != 0 and outcome["failed"] else "NOT caught"
                failed = "<br>".join("`%s`" % f.split("::", 1)[-1] for f in outcome["failed"])  # type: ignore[union-attr]
            lines.append("| %s | %s | %s | %s |" % (layer, fix, verdict, failed))
    return "\n".join(lines) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    parser.add_argument("--layer", choices=sorted(LAYERS), action="append", default=[])
    parser.add_argument("--all", action="store_true", help="every layer, every fix")
    parser.add_argument("--fix", action="append", default=[], help="only these fixes (baseline always runs)")
    parser.add_argument("--python", default=sys.executable, help="interpreter with the test dependencies installed")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)
    layers = sorted(LAYERS) if args.all else args.layer
    if not layers:
        parser.error("pass --layer or --all")

    results: Dict[str, Dict[str, Dict[str, object]]] = {}
    for layer in layers:
        fixes = ["baseline", *(f for f in LAYERS[layer][2] if not args.fix or f in args.fix)]
        results[layer] = {}
        for fix in fixes:
            outcome = run_one(layer, fix, args.python)
            results[layer][fix] = outcome
            print(
                "%-9s %-15s exit=%s failed=%d %s"
                % (layer, fix, outcome.get("exit", "-"), len(outcome.get("failed", [])), outcome.get("error", "")),  # type: ignore[arg-type]
                flush=True,
            )
    if args.json:
        args.json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    table = render(results)
    if args.markdown:
        args.markdown.write_text(table, encoding="utf-8")
    sys.stdout.write(table)
    bad = [
        (layer, fix)
        for layer, fixes in results.items()
        for fix, outcome in fixes.items()
        if "error" in outcome
        or (fix == "baseline" and outcome["exit"] != 0)
        or (fix != "baseline" and (outcome["exit"] == 0 or not outcome["failed"]))
    ]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
