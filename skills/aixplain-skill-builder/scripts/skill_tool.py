#!/usr/bin/env python3
"""Scaffold and check skills for Koder and the aiXplain platform.

    python3 skill_tool.py new <name> --target koder|platform --dir <parent>
    python3 skill_tool.py check <skill-folder> [--target koder|platform|auto]

`check` exits 1 when it finds an error, 0 otherwise (warnings do not fail it).
Standard library only; uses PyYAML when installed for a stricter frontmatter parse.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "..", "templates")

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
KODER_KEYS = {"name", "description", "paths", "license", "compatibility", "metadata"}
PLATFORM_KEYS = {"name", "description", "activation", "tools", "requires", "required_tools",
                 "license", "compatibility", "metadata"}
TOOL_TYPES = {"aixplain", "script", "mcp", "builtin"}
# Example values that are clearly not real credentials.
PLACEHOLDER_RE = re.compile(r"(?i)(your[_-]|<[^>]+>|x{4,}|\*{3,}|\.\.\.|…|changeme|example|placeholder|dummy|"
                            r"://[^/\s:@]+:(password|pass|secret|pwd)@)")
TEXT_EXT = {".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml", ".sh", ".js", ".ts", ".csv", ".env", ".ini", ".cfg"}

SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Slack token", re.compile(r"\bxox[abpors]-[A-Za-z0-9-]{10,}")),
    ("credentials in a URL", re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s:@]{6,}@")),
    ("hard-coded key/token/secret",
     re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"][A-Za-z0-9_\-./+]{16,}['\"]")),
    ("long hex string (aiXplain keys look like this)", re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{40,}(?![0-9a-fA-F])")),
]


# --------------------------------------------------------------------------- #
# Frontmatter
# --------------------------------------------------------------------------- #
def split_frontmatter(text):
    """Return (frontmatter_text, body) or (None, text) when there is none."""
    stripped = text.lstrip("﻿")
    if not stripped.startswith("---"):
        return None, text
    match = re.search(r"\n---[ \t]*(\n|$)", stripped[3:])
    if not match:
        return None, text
    front = stripped[3:3 + match.start()]
    body = stripped[3 + match.end():]
    return front, body


def _scalar(value):
    value = value.strip()
    if not value:
        return None
    if value[0] in "\"'" and value[-1] == value[0] and len(value) >= 2:
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        return [_scalar(v) for v in value[1:-1].split(",") if v.strip()]
    if value.startswith("{"):
        return {"__raw__": value}
    return value.split(" #", 1)[0].strip()


def parse_frontmatter(front):
    """Parse YAML frontmatter. Returns (data, parser_name, error)."""
    try:
        import yaml  # type: ignore
        try:
            data = yaml.safe_load(front) or {}
        except yaml.YAMLError as exc:
            return None, "pyyaml", str(exc).splitlines()[0]
        if not isinstance(data, dict):
            return None, "pyyaml", "frontmatter is not a key: value mapping"
        return data, "pyyaml", None
    except ImportError:
        pass
    # Minimal fallback: top-level scalars, inline lists, block lists of scalars,
    # and quoted values continued on indented lines. Nested blocks are kept raw.
    data, key, raw = {}, None, []
    for line in front.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([A-Za-z_][\w-]*):(.*)$", line)
        if top and not line.startswith((" ", "\t")):
            if key and raw:
                data[key] = {"__raw__": "\n".join(raw)}
            key, raw = top.group(1), []
            data[key] = _scalar(top.group(2))
            continue
        if key is None:
            return None, "fallback", f"cannot parse line: {line!r}"
        item = re.match(r"^\s+-\s+(.*)$", line)
        if isinstance(data.get(key), (list, type(None))) and item and ":" not in item.group(1):
            data[key] = (data[key] or []) + [_scalar(item.group(1))]
        elif isinstance(data.get(key), str):
            data[key] = (data[key] + " " + line.strip()).strip()
            if data[key][0] in "\"'" and data[key].endswith(data[key][0]):
                data[key] = data[key][1:-1]
        else:
            raw.append(line)
    if key and raw:
        data[key] = {"__raw__": "\n".join(raw)}
    return data, "fallback", None


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def find_entry(folder):
    names = os.listdir(folder)
    if "SKILL.md" in names:
        return os.path.join(folder, "SKILL.md")
    for n in sorted(names):
        if n.lower() == "skill.md":
            return os.path.join(folder, n)
    return None


def check_tools(tools, folder, rep):
    if isinstance(tools, dict) and "__raw__" in tools:
        rep.warn("`tools:` present but not checked in depth (install PyYAML: pip install pyyaml).")
        return
    if not isinstance(tools, list):
        rep.error("`tools:` must be a list of tool entries.")
        return
    for i, tool in enumerate(tools, 1):
        where = f"tools[{i}]"
        if not isinstance(tool, dict):
            rep.error(f"{where} must be a mapping with a `type:`.")
            continue
        kind = tool.get("type")
        if kind not in TOOL_TYPES:
            rep.error(f"{where}: type {kind!r} is not one of {sorted(TOOL_TYPES)}.")
            continue
        if kind == "aixplain" and not tool.get("tool_id"):
            rep.error(f"{where}: an aixplain tool needs `tool_id` (asset id or team/name path).")
        if kind == "script":
            for k in ("name", "description", "script_file"):
                if not tool.get(k):
                    rep.error(f"{where}: a script tool needs `{k}`.")
            sf = tool.get("script_file")
            if sf and not os.path.isfile(os.path.join(folder, sf)):
                rep.error(f"{where}: script_file {sf!r} does not exist in the skill folder.")
            req = tool.get("required") or []
            params = tool.get("parameters") or {}
            for r in req if isinstance(req, list) else []:
                if isinstance(params, dict) and r not in params:
                    rep.error(f"{where}: required parameter {r!r} is not in `parameters`.")
        if kind == "mcp" and not (tool.get("url") or tool.get("command")):
            rep.error(f"{where}: an mcp tool needs `url` or `command`.")
    if tools:
        rep.warn("The SDK does not validate `tools:`; run the agent once after publishing to confirm they bind.")


def linked_paths(body):
    found = set()
    for m in re.finditer(r"\]\(([^)\s#]+)\)", body):
        found.add(m.group(1))
    for m in re.finditer(r"`((?:references|scripts|templates|assets|resources)/[^`\s]+)`", body):
        found.add(m.group(1))
    return {p for p in found if "://" not in p and not p.startswith(("/", "~", "<", "mailto:")) and "…" not in p and "<" not in p and "*" not in p}


def scan_secrets(folder, rep):
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv"}]
        for f in files:
            path = os.path.join(root, f)
            rel = os.path.relpath(path, folder)
            if f == ".env" or f.endswith((".pem", ".key")):
                rep.error(f"{rel}: credential file inside the skill folder — remove it.")
                continue
            if os.path.splitext(f)[1].lower() not in TEXT_EXT:
                continue
            try:
                with open(path, encoding="utf-8", errors="ignore") as fh:
                    lines = fh.read().splitlines()
            except OSError:
                continue
            for n, line in enumerate(lines, 1):
                for label, rx in SECRET_PATTERNS:
                    if rx.search(line) and not PLACEHOLDER_RE.search(rx.search(line).group(0)):
                        msg = f"{rel}:{n}: possible secret ({label})."
                        # A long hex string is often a public asset id; flag it, don't fail.
                        (rep.warn if label.startswith("long hex") else rep.error)(
                            msg + (" Fine if it is an asset id." if label.startswith("long hex") else
                                   " Read it from the environment instead."))
                        break


def check(folder, target, rep):
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        rep.error(f"{folder} is not a folder.")
        return None
    entry = find_entry(folder)
    if not entry:
        rep.error("No SKILL.md in the folder.")
        return None
    if os.path.basename(entry) != "SKILL.md":
        rep.warn(f"Entry file is {os.path.basename(entry)!r}; prefer exactly 'SKILL.md'.")
    with open(entry, encoding="utf-8") as fh:
        text = fh.read()
    front, body = split_frontmatter(text)
    if front is None:
        rep.error("SKILL.md has no frontmatter (a '---' block at the top with name and description).")
        return None
    data, parser, err = parse_frontmatter(front)
    if err:
        rep.error(f"Frontmatter does not parse ({parser}): {err}. Quote values that contain ': '.")
        return None

    if target == "auto":
        target = "platform" if ("tools" in data or "activation" in data) else "koder"

    # name
    name = data.get("name")
    folder_name = os.path.basename(folder)
    if not name:
        rep.error("`name:` is missing — Koder drops a skill without one.")
    elif not isinstance(name, str) or not NAME_RE.match(name):
        rep.error(f"`name: {name}` must be lowercase letters, digits and hyphens.")
    else:
        if len(name) > 64:
            rep.error(f"`name` is {len(name)} characters; the limit is 64.")
        if name != folder_name:
            rep.error(f"`name: {name}` does not match the folder name {folder_name!r}.")

    # description
    desc = data.get("description")
    if not desc or not isinstance(desc, str) or not desc.strip():
        rep.error("`description:` is missing — the skill would never be offered to the model.")
    else:
        d = desc.strip()
        if "…" in d or "{{" in d:
            rep.error("`description` still contains template placeholders.")
        if len(d) < 60:
            rep.warn(f"`description` is only {len(d)} characters; say what it does AND when to use it.")
        if len(d) > 1024:
            rep.warn(f"`description` is {len(d)} characters; keep it under ~1024 (it is in every prompt).")
        if not re.search(r"(?i)\b(use (when|for|whenever|this)|when the user|trigger)", d):
            rep.warn("`description` has no 'Use when…' clause; say when the skill should load.")
        if re.match(r"(?i)^(i|we)\b", d):
            rep.warn("Write the description in the third person ('Use when…'), not 'I…'.")

    # paths
    if "paths" in data:
        p = data["paths"]
        if isinstance(p, str):
            p = [p]
        if not isinstance(p, list) or not all(isinstance(x, str) and x.strip() for x in p):
            rep.error("`paths:` must be a glob string or a list of glob strings.")
        elif target == "platform":
            rep.warn("`paths:` is a Koder-only key; the aiXplain platform ignores it.")

    # target-specific keys
    allowed = KODER_KEYS if target == "koder" else PLATFORM_KEYS | {"paths"}
    for key in data:
        if key not in allowed:
            if target == "koder" and key in PLATFORM_KEYS:
                rep.warn(f"`{key}:` is ignored by Koder (it is an aiXplain platform key).")
            else:
                rep.warn(f"Unknown frontmatter key `{key}:`.")
    if target == "platform":
        act = data.get("activation")
        if act is not None and act not in ("conditional", "always"):
            rep.error(f"`activation: {act}` must be 'conditional' or 'always'.")
        if "tools" in data:
            check_tools(data["tools"], folder, rep)

    # body
    lines = body.strip().splitlines()
    if not lines:
        rep.error("SKILL.md has no body — nothing for the model to follow once loaded.")
    elif len(lines) > 500:
        rep.warn(f"Body is {len(lines)} lines; move detail into references/ (aim for under ~400).")
    if "{{" in body or re.search(r"^\s*\d+\.\s*…\s*$", body, re.M):
        rep.warn("Body still contains template placeholders.")
    for rel in sorted(linked_paths(body)):
        if not os.path.exists(os.path.join(folder, rel)):
            rep.error(f"Body refers to {rel!r}, which is not in the skill folder.")

    scan_secrets(folder, rep)
    return target, parser


# --------------------------------------------------------------------------- #
# new
# --------------------------------------------------------------------------- #
def new(name, target, parent, force):
    if not NAME_RE.match(name) or len(name) > 64:
        sys.exit(f"error: {name!r} is not a valid skill name (lowercase letters, digits, hyphens; ≤64).")
    folder = os.path.join(os.path.abspath(os.path.expanduser(parent)), name)
    if os.path.exists(os.path.join(folder, "SKILL.md")) and not force:
        sys.exit(f"error: {folder}/SKILL.md already exists (use --force to overwrite).")
    os.makedirs(os.path.join(folder, "references"), exist_ok=True)
    os.makedirs(os.path.join(folder, "scripts"), exist_ok=True)
    with open(os.path.join(TEMPLATES, f"{target}-SKILL.md"), encoding="utf-8") as fh:
        content = fh.read()
    title = name.replace("-", " ").capitalize()
    content = content.replace("{{name}}", name).replace("{{title}}", title)
    with open(os.path.join(folder, "SKILL.md"), "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"Created {folder}/SKILL.md (+ references/, scripts/)")
    print("Next: write the description and body, then run:")
    print(f"  python3 {os.path.relpath(__file__)} check {folder} --target {target}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="scaffold a skill folder")
    n.add_argument("name")
    n.add_argument("--target", choices=["koder", "platform"], required=True)
    n.add_argument("--dir", default=".", help="parent folder (default: current folder)")
    n.add_argument("--force", action="store_true")
    c = sub.add_parser("check", help="validate a skill folder")
    c.add_argument("folder")
    c.add_argument("--target", choices=["koder", "platform", "auto"], default="auto")
    args = ap.parse_args()

    if args.cmd == "new":
        new(args.name, args.target, args.dir, args.force)
        return
    rep = Report()
    result = check(args.folder, args.target, rep)
    if result:
        print(f"target: {result[0]}   frontmatter parser: {result[1]}")
    for e in rep.errors:
        print(f"ERROR  {e}")
    for w in rep.warnings:
        print(f"warn   {w}")
    print(f"\n{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
