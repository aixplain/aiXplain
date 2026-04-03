#!/usr/bin/env python3
"""Generate llms.txt and llms-full.txt bundles for aiXplain SDK v2 docs."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DOCS_ROOT = REPO_ROOT / "docs"
SIDEBAR_PATH = DOCS_ROOT / "api-reference/python/api_sidebar.js"
LLMS_INDEX_PATH = DOCS_ROOT / "llms.txt"
LLMS_FULL_PATH = DOCS_ROOT / "api-reference/python/aixplain/v2/llms-full.txt"
TARGET_LABEL = "aixplain.v2"
TARGET_PREFIX = "api-reference/python/aixplain/v2/"


def _flatten_doc_ids(items: list[object]) -> list[str]:
    doc_ids: list[str] = []
    for item in items:
        if isinstance(item, str):
            doc_ids.append(item)
            continue

        if isinstance(item, dict):
            doc_ids.extend(_flatten_doc_ids(item.get("items", [])))

    return doc_ids


def _find_category(items: list[object], label: str) -> dict | None:
    for item in items:
        if isinstance(item, dict):
            if item.get("label") == label:
                return item

            found = _find_category(item.get("items", []), label)
            if found is not None:
                return found

    return None


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        return {}, content

    match = re.match(r"^---\n(.*?)\n---\n?", content, flags=re.DOTALL)
    if match is None:
        return {}, content

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')

    return metadata, content[match.end() :].lstrip()


def _normalize_doc_body(content: str) -> tuple[str, str]:
    metadata, body = _parse_frontmatter(content)
    title = metadata.get("title", "").strip() or "Untitled"
    body = html.unescape(body)
    body = body.replace("\\_", "_").replace("\\{", "{").replace("\\}", "}")
    body = body.rstrip()
    return title, body


def _get_v2_docs() -> list[tuple[str, str, str]]:
    sidebar = json.loads(SIDEBAR_PATH.read_text())
    category = _find_category(sidebar.get("items", []), TARGET_LABEL)
    if category is None:
        raise ValueError(f"Could not find sidebar category {TARGET_LABEL!r} in {SIDEBAR_PATH}")

    doc_ids = [
        doc_id
        for doc_id in _flatten_doc_ids(category.get("items", []))
        if doc_id.startswith(TARGET_PREFIX)
    ]
    if not doc_ids:
        raise ValueError(f"No documents found for prefix {TARGET_PREFIX!r}")

    docs: list[tuple[str, str, str]] = []
    for doc_id in doc_ids:
        doc_path = DOCS_ROOT / f"{doc_id}.md"
        if not doc_path.exists():
            raise FileNotFoundError(f"Sidebar entry points to a missing doc: {doc_path}")

        title, body = _normalize_doc_body(doc_path.read_text())
        docs.append((doc_id, title, body))

    return docs


def _extract_summary(body: str) -> str:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", body) if paragraph.strip()]
    for paragraph in paragraphs:
        if paragraph.startswith("#") or paragraph.startswith("```") or paragraph.startswith("[[view_source]]"):
            continue

        summary = " ".join(line.strip() for line in paragraph.splitlines()).strip()
        if summary:
            return summary

    return "Reference documentation."


def build_llms_index() -> str:
    docs = _get_v2_docs()
    sections = [
        "# aiXplain Docs",
        "",
        "> LLM-readable entrypoint for the aiXplain Python SDK v2 reference.",
        "",
        "Use `api-reference/python/aixplain/v2/llms-full.txt` when you want the complete SDK v2 reference in one context window.",
        "",
        "## Recommended",
        "",
        "- [SDK v2 full reference](api-reference/python/aixplain/v2/llms-full.txt): Complete concatenated aiXplain Python SDK v2 API reference.",
        "- [SDK v2 landing page](api-reference/python/aixplain/v2/init.md): Package overview for `aixplain.v2`.",
        "",
        "## SDK v2 Modules",
        "",
    ]

    for doc_id, title, body in docs:
        sections.append(f"- [{title}]({doc_id}.md): {_extract_summary(body)}")

    sections.extend(
        [
            "",
            "## Regeneration",
            "",
            "- Run `python generate_llms_full.py` from the repository root.",
        ]
    )

    return "\n".join(sections).rstrip() + "\n"


def build_llms_full() -> str:
    docs = _get_v2_docs()

    sections = [
        "# aiXplain SDK v2 Reference",
        "",
        "This file concatenates the aiXplain Python SDK v2 reference into one text bundle for LLM ingestion.",
        "",
        "Regenerate with `python generate_llms_full.py` from the repository root.",
    ]

    for doc_id, title, body in docs:
        sections.extend(
            [
                "",
                "---",
                "",
                f"## {title}",
                "",
                f"Source: `{doc_id}`",
                "",
                body or "_No content._",
            ]
        )

    return "\n".join(sections).rstrip() + "\n"


def main() -> None:
    LLMS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    LLMS_FULL_PATH.parent.mkdir(parents=True, exist_ok=True)

    LLMS_INDEX_PATH.write_text(build_llms_index())
    LLMS_FULL_PATH.write_text(build_llms_full())

    print(f"Wrote {LLMS_INDEX_PATH.relative_to(REPO_ROOT)}")
    print(f"Wrote {LLMS_FULL_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
