#!/usr/bin/env python3

import os
import re
import json

from docs_rst_processor import convert_rst, split_fences

# Docusaurus compiles .md as MDX, which means: indented code blocks are disabled
# (code must use ``` fences), a raw "<" in prose starts a JSX tag, "{" starts a
# JSX expression, and HTML entities are never decoded inside code spans or
# fences. So escaping has to happen on prose only, after the code has been carved
# out -- escaping with just the fences carved out is what put a literal
# "\{name: value}" inside inline code spans.

# Entities pydoc-markdown used to emit before we turned escape_html_in_docstring
# off. Substituted in one pass, so "&amp;lt;" degrades to "&lt;", not to "<".
ENTITIES = {
    "&quot;": '"',
    "&#x27;": "'",
    "&#39;": "'",
    "&apos;": "'",
    "&lt;": "<",
    "&gt;": ">",
    "&amp;": "&",
}
ENTITY_RE = re.compile("|".join(map(re.escape, ENTITIES)))

# Every bare "<", not only "<" before a letter: MDX fires its JSX parser on the
# character itself, so ("<") and <<COLUMN>> fail just like <name>. Both patterns
# capture the backslash run in front, because an even run means unescaped.
BRACE_RE = re.compile(r"(?<!\\)(\\*)\{")
JSX_RE = re.compile(r"(?<!\\)(\\*)<")
TICKS_RE = re.compile(r"`+")


def split_code_spans(text):
    """
    Split text into (is_code, chunk) pairs using CommonMark backtick pairing:
    a run of N backticks opens a span closed by the next run of exactly N.
    A span cannot cross a blank line, or one stray backtick swallows the file.
    """
    segments = []
    pos = 0
    while pos < len(text):
        opener = TICKS_RE.search(text, pos)
        if not opener:
            break

        limit = text.find("\n\n", opener.end())
        limit = len(text) if limit == -1 else limit

        closer, cursor = None, opener.end()
        while True:
            candidate = TICKS_RE.search(text, cursor)
            if not candidate or candidate.start() > limit:
                break
            if candidate.group(0) == opener.group(0):
                closer = candidate
                break
            cursor = candidate.end()

        if closer is None:
            segments.append((False, text[pos:opener.end()]))
            pos = opener.end()
            continue

        if opener.start() > pos:
            segments.append((False, text[pos:opener.start()]))
        segments.append((True, text[opener.start():closer.end()]))
        pos = closer.end()

    if pos < len(text):
        segments.append((False, text[pos:]))
    return segments


def escape_prose(text):
    """Escape "{" and "<" so MDX does not read them as JSX. Prose only."""
    for pattern, char in ((BRACE_RE, "{"), (JSX_RE, "<")):
        text = pattern.sub(
            lambda m, c=char: m.group(1) + ("\\" + c if len(m.group(1)) % 2 == 0 else c),
            text,
        )
    return text


def transform_markdown(text):
    """
    1. Decode HTML entities that were escaped before markdown rendering
    2. Convert RST literal blocks, roles and directives to markdown
    3. Escape MDX characters in prose, never inside code spans or fences
    """
    match = re.match(r"\A---\n.*?\n---\n", text, re.DOTALL)
    frontmatter, body = (match.group(0), text[match.end():]) if match else ("", text)

    body = convert_rst(ENTITY_RE.sub(lambda m: ENTITIES[m.group(0)], body))

    out = []
    for is_fence, chunk in split_fences(body):
        if is_fence:
            out.append(chunk)
            continue
        for is_code, piece in split_code_spans(chunk):
            # A backslash is literal inside a code span, so "\{" renders one.
            out.append(piece.replace("\\{", "{") if is_code else escape_prose(piece))

    return frontmatter + "".join(out)


def is_private(name):
    """A single leading underscore marks a private module. __init__ is not one."""
    return name.startswith("_") and not name.startswith("__")


def rename_files(docs_dir="docs/api-reference/python"):
    """
    1. Rename __init__.md files to init.md
    2. Delete pages for private modules
    """
    renamed_init_files = 0
    removed_private_files = 0

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file == "__init__.md":
                os.rename(os.path.join(root, file), os.path.join(root, "init.md"))
                renamed_init_files += 1

            # A private module is an implementation detail, not API. pydoc-markdown
            # has no option to skip one -- FilterProcessor.exclude_private applies
            # to members, and modules are exempt from filtering entirely -- so the
            # page is dropped here instead.
            elif file.endswith(".md") and is_private(file[:-len(".md")]):
                os.remove(os.path.join(root, file))
                removed_private_files += 1

    print(f"Renamed {renamed_init_files} __init__.md files to init.md")
    print(f"Removed {removed_private_files} pages for private modules")


def process_content(docs_dir="docs/api-reference/python"):
    """
    Process markdown content:
    1. Decode HTML entities, convert RST, escape braces outside code
    """
    modified_files = 0

    for root, _, files in os.walk(docs_dir):
        for file in files:
            # A generated page is named after its module, and a module name
            # cannot contain a dot, so a dotted stem (client.ar.md) marks a
            # hand-written file such as a translation. Those are not ours.
            if not file.endswith(".md") or "." in file[:-len(".md")]:
                continue

            file_path = os.path.join(root, file)
            with open(file_path, "r") as f:
                content = f.read()

            updated = transform_markdown(content)
            if updated != content:
                with open(file_path, "w") as f:
                    f.write(updated)
                modified_files += 1

    print(f"Processed {modified_files} markdown files (RST to markdown, MDX-safe escaping)")


def mark_empty_init_files(docs_dir="docs/api-reference/python"):
    """
    Mark empty init.md files as drafts
    """
    modified_files = 0

    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file == "init.md":
                file_path = os.path.join(root, file)

                with open(file_path, "r") as f:
                    content = f.read()

                # Remove frontmatter
                frontmatter_pattern = re.compile(r"^---\n.*?---\n", re.DOTALL)
                content_without_frontmatter = frontmatter_pattern.sub("", content).strip()

                marks = len(re.findall(r"^draft:\s*true$", content, re.M))
                if content_without_frontmatter or marks == 1:
                    continue

                if marks:
                    # Collapse marks an earlier run stacked up. A repeated YAML
                    # key is a parse error, so the page breaks the site build.
                    modified_content = re.sub(r"^draft:\s*true\n", "", content, count=marks - 1, flags=re.M)
                else:
                    modified_content = re.sub(r"^(---\n)", r"\1draft: true\n", content, count=1)

                with open(file_path, "w") as f:
                    f.write(modified_content)

                modified_files += 1

    print(f"Marked {modified_files} empty init files as drafts")


def configure_sidebar(sidebar_path="docs/api-reference/python/api_sidebar.js"):
    """
    Configure sidebar:
    1. Fix sidebar references for files renamed or removed by rename_files
    2. Make top-level categories non-collapsible
    3. Add landing page link
    """
    with open(sidebar_path, "r") as f:
        content = f.read()

    init_replacements = content.count("__init__")

    # Mirror what rename_files did on disk, or an entry points at a file that is
    # no longer there, which Docusaurus treats as a build error.
    def rewrite(node):
        if isinstance(node, str):
            head, _, name = node.rpartition("/")
            if name == "__init__":
                return f"{head}/init" if head else "init"
            return node
        if isinstance(node, list):
            return [rewrite(item) for item in node
                    if not (isinstance(item, str) and is_private(item.rpartition("/")[2]))]
        if isinstance(node, dict):
            return {k: rewrite(v) if k == "items" else v for k, v in node.items()}
        return node

    sidebar_data = rewrite(json.loads(content))

    # 2. Make top-level categories non-collapsible
    sidebar_data["collapsible"] = False
    for item in sidebar_data.get("items", []):
        if isinstance(item, dict) and item.get("type") == "category":
            item["collapsible"] = False

    # 3. Add landing page link
    sidebar_data["link"] = {"type": "doc", "id": "api-reference/python/python"}

    with open(sidebar_path, "w") as f:
        json.dump(sidebar_data, f, indent=2)

    print(f"Updated {init_replacements} __init__ references to init in sidebar")
    print(f"Added collapsible: false to top-level categories")
    print(f"Added landing page link to sidebar")


def main():
    """
    Execute all post-processing steps for documentation
    """
    print("Starting documentation post-processing...")

    os.makedirs("docs/api-reference/python", exist_ok=True)

    # 1. Rename files
    rename_files()

    # 2. Process content
    process_content()

    # 3. Mark empty init files
    mark_empty_init_files()

    # 4. Configure sidebar
    configure_sidebar()

    print("Documentation post-processing complete!")


if __name__ == "__main__":
    main()
