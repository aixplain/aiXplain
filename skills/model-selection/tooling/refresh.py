"""Refresh the model-selection skill's catalog snapshot and write a review report.

Reads every LLM from the aixplain Marketplace Search MCP, writes
references/catalog.json, and compares it with the previous snapshot and
references/tiers.json. The report is Markdown, used as the weekly PR body.

    AIXPLAIN_API_KEY=... python skills/model-selection/tooling/refresh.py --report report.md

Standard library only, so the workflow needs no install step.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

MCP_URL = "https://models-mcp.aixplain.com/mcp/6960f934f316da19e5f22494"
SKILL_DIR = Path(__file__).resolve().parent.parent
CATALOG = SKILL_DIR / "references" / "catalog.json"
TIERS = SKILL_DIR / "references" / "tiers.json"
PAGE_SIZE = 100
# Catalog per-token prices sit around 1e-8 to 1e-4; above this the unit is wrong.
SUSPECT_PRICE = 0.001


class Mcp:
    """Minimal streamable-HTTP MCP client: initialize once, then call tools."""

    def __init__(self, url, api_key):
        self.url = url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        self.next_id = 1
        self._post("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "model-selection-refresh", "version": "1"},
        })
        self._post("notifications/initialized", None, notify=True)

    def _post(self, method, params, notify=False):
        message = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        if not notify:
            message["id"] = self.next_id
            self.next_id += 1
        request = urllib.request.Request(
            self.url, data=json.dumps(message).encode(), headers=self.headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.headers["Mcp-Session-Id"] = session
            body = response.read().decode()
        if notify:
            return None
        return _parse_body(body)

    def call(self, tool, arguments):
        reply = self._post("tools/call", {"name": tool, "arguments": arguments})
        if "error" in reply:
            raise RuntimeError(f"{tool}: {reply['error']}")
        result = reply["result"]
        if result.get("isError"):
            raise RuntimeError(f"{tool}: {result['content']}")
        return json.loads(result["content"][0]["text"])


def _parse_body(body):
    """A reply is plain JSON or a server-sent event stream; take the JSON-RPC response."""
    if body.lstrip().startswith("{"):
        return json.loads(body)
    for line in body.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line[5:])
            if "id" in payload:
                return payload
    raise RuntimeError(f"No JSON-RPC response in: {body[:200]}")


def fetch_llms(mcp):
    models, page = [], 0
    while True:
        reply = mcp.call("search_models", {
            "query": "", "categories": ["LLM"], "page_size": PAGE_SIZE, "page_number": page,
        })
        models += reply["results"]
        page += 1
        if page >= reply["stats"]["pages_count"]:
            return models


def snapshot(models):
    """Keep only the fields worth diffing, keyed by id and sorted for stable diffs."""
    rows = {}
    for m in models:
        pricing = m.get("pricing") or {}
        rows[m["id"]] = {
            "path": m["path"],
            "name": m["name"],
            "input_price": pricing.get("input_price"),
            "output_price": pricing.get("output_price"),
            "zdr": m.get("zdr"),
        }
    return dict(sorted(rows.items(), key=lambda item: item[1]["path"]))


def build_report(old, new, tiers):
    reviewed = tiers["models"]
    excluded = tiers.get("excluded", {})
    sections = []

    def section(title, lines):
        if lines:
            sections.append(f"### {title} ({len(lines)})\n\n" + "\n".join(lines))

    def label(model_id, row):
        return f"`{row['path']}` ({row['name']}, `{model_id}`)"

    if old:
        added = [i for i in new if i not in old]
        section("New on the marketplace: add to tiers.json or excluded",
                [f"- {label(i, new[i])}" for i in added if i not in reviewed and i not in excluded])

    section("In tiers.json but gone from the marketplace: remove",
            [f"- `{row['path']}` (`{i}`)" for i, row in reviewed.items() if i not in new])

    if old:
        changes = []
        for i, row in new.items():
            before = old.get(i)
            if not before:
                continue
            for field in ("input_price", "output_price", "zdr"):
                if before[field] != row[field]:
                    changes.append(f"- {label(i, row)}: {field} {before[field]} → {row[field]}")
        section("Price or ZDR changed", changes)

    section("Prices that look like the wrong unit (above 0.001 per token)", [
        f"- {label(i, row)}: in {row['input_price']} / out {row['output_price']}"
        for i, row in new.items()
        if any((row[f] or 0) > SUSPECT_PRICE for f in ("input_price", "output_price"))
    ])

    untiered = [i for i in new if i not in reviewed and i not in excluded]
    unreviewed = sum(1 for row in reviewed.values() if not row.get("reviewed"))
    summary = (
        f"{len(new)} LLMs on the marketplace. {len(reviewed)} tiered "
        f"({unreviewed} still resting on the vendor description), {len(untiered)} untiered."
    )
    if not old:
        summary += " First snapshot: nothing to compare with yet."
    body = "\n\n".join(sections) or "Nothing needs review this week."
    return f"## Model selection: weekly refresh\n\n{summary}\n\n{body}\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", type=Path, help="write the Markdown report here")
    args = parser.parse_args()

    api_key = os.environ.get("AIXPLAIN_API_KEY")
    if not api_key:
        sys.exit("Set AIXPLAIN_API_KEY.")

    new = snapshot(fetch_llms(Mcp(MCP_URL, api_key)))
    old = json.loads(CATALOG.read_text()) if CATALOG.exists() else {}
    tiers = json.loads(TIERS.read_text())

    CATALOG.write_text(json.dumps(new, indent=2) + "\n")
    report = build_report(old, new, tiers)
    if args.report:
        args.report.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
