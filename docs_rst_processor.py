#!/usr/bin/env python3

import ast
import dataclasses
import re
import textwrap

# Converts the reStructuredText left in docstrings (literal blocks, cross-reference
# roles, directives) into markdown. It runs as a pydoc-markdown processor, placed
# ahead of the built-in "smart" one in pydoc-markdown.yml, because GoogleProcessor
# calls line.strip() on every docstring line outside a ``` fence -- and an RST
# literal block is defined entirely by its indentation. After that strip the block
# sits at column 0 and is indistinguishable from prose, so post-processing cannot
# recover it. Fenced blocks are passed through untouched, so what we emit here
# survives the rest of the pipeline.
#
# post_process_docs.py imports convert_rst and split_fences from here, and runs
# under the plain system interpreter, so pydoc-markdown is an optional import.
try:
    import docspec
    from pydoc_markdown.interfaces import Processor, Resolver

    HAVE_PYDOC_MARKDOWN = True
except ImportError:
    HAVE_PYDOC_MARKDOWN = False


FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")

# :class:`Target`, :py:meth:`~pkg.mod.Cls.method`, :exc:`Title <ref>`. The role
# name is matched generically so an unanticipated role is converted, not leaked.
ROLE_RE = re.compile(r":(?:py:)?[a-zA-Z][a-zA-Z0-9_+-]*:(`{1,2})([^`]+?)\1")

DIRECTIVE_RE = re.compile(r"^([ \t]*)\.\.[ \t]+([a-zA-Z][a-zA-Z0-9_-]*)::[ \t]*(.*)$")

VERSIONED = {
    "deprecated": "Deprecated",
    "versionadded": "Added in version",
    "versionchanged": "Changed in version",
    "versionremoved": "Removed in version",
}

ADMONITIONS = {
    "note": "Note",
    "warning": "Warning",
    "caution": "Caution",
    "important": "Important",
    "tip": "Tip",
    "danger": "Danger",
    "attention": "Attention",
    "seealso": "See also",
}

# A paragraph introducing a literal block. ".." is excluded so a directive is
# never mistaken for a lead-in.
LITERAL_LEADIN_RE = re.compile(r"^([ \t]*)((?!\.\.[ \t]).*?)([ \t]*)::[ \t]*$")

# "Example usage:", "**Example**:", "Usage:" -- an example block without RST's
# "::" marker. The body is still indented code, and MDX has no indented code
# blocks, so it renders as prose: "#" comments become <h1>, ">>>" a blockquote.
# Only example-ish labels match, so "**Arguments**:" and its list are left alone.
EXAMPLE_LEADIN_RE = re.compile(
    r"^([ \t]*)(\**\s*"
    r"(?:[A-Za-z][A-Za-z ]*\b(?:example|examples|usage|sample)\b|"
    r"(?:example|examples|usage|sample)\b[A-Za-z ]*)"
    r"\s*\**)[ \t]*:[ \t]*$",
    re.IGNORECASE,
)

# Signals that a block is Python rather than a diagram or a data dump.
PYTHONISH_RE = re.compile(r"(^|\n)\s*(from|import|def|class|@|>>>)\s|[=(]")

# Structural giveaways that a block is Python even when it does not parse:
# example code is routinely elided, so "def save(self):" followed by only a
# comment raises IndentationError and ast.parse alone would reject real code.
CODE_SHAPE_RE = re.compile(r"^[ \t]*(?:>>>|@\w|def\s|class\s|import\s|from\s+\w+\s+import\b)", re.M)

# Lines ending a de-indented ("flat") literal block. "#" is deliberately absent:
# a flat Python block's comments start with "#" and would end the block at once.
FLAT_TERMINATORS = (
    re.compile(r"^#{1,6}[ \t]+\S"),           # markdown heading
    re.compile(r"^<a\s+id="),                 # pydoc-markdown anchor
    re.compile(r"^\*\*[^*]+\*\*:?\s*$"),      # **Arguments**: section label
    re.compile(r"^(```|~~~)"),                # a fence
    re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$"), # thematic break
    re.compile(r"^\[\[view_source\]\]"),      # pydoc-markdown source link
    re.compile(r"^[-*+][ \t]+\S"),            # list item
    re.compile(r"^>[ \t]"),                   # block quote
)


def split_fences(text):
    """Split text into (is_fence, chunk) pairs, preserving every character."""
    out = []
    buf = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    for line in text.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        if not in_fence:
            if match:
                if buf:
                    out.append((False, "".join(buf)))
                    buf = []
                in_fence = True
                fence_char = match.group(1)[0]
                fence_len = len(match.group(1))
            buf.append(line)
            continue

        buf.append(line)
        # A closing fence: same character, at least as long, no info string.
        if (match and match.group(1)[0] == fence_char
                and len(match.group(1)) >= fence_len and not match.group(2).strip()):
            out.append((True, "".join(buf)))
            buf = []
            in_fence = False

    if buf:
        out.append((in_fence, "".join(buf)))
    return out


def map_outside_fences(text, fn):
    """Apply fn to every non-fenced chunk, leaving fences untouched."""
    return "".join(chunk if is_fence else fn(chunk) for is_fence, chunk in split_fences(text))


def indent_width(line):
    stripped = line.lstrip(" \t")
    return len(line[:len(line) - len(stripped)].expandtabs())


def convert_roles(text):
    """
    Replace Sphinx cross-reference roles with inline code spans. There is no
    reliable link target for these symbols, so a code span is the honest
    rendering rather than inventing a URL that would 404.
    """
    def repl(match):
        target = match.group(2).strip()

        # Explicit-title form: "Some Title <actual.target>"
        title = re.match(r"^(.*?)\s*<([^<>]+)>$", target, re.DOTALL)
        if title:
            target = title.group(1).strip() or title.group(2).strip()

        # A leading "~" means show only the last dotted component.
        if target.startswith("~"):
            target = target[1:].strip().rsplit(".", 1)[-1]

        target = target.lstrip("!").strip()
        if not target:
            return match.group(0)
        return target if "`" in target else f"`{target}`"

    return map_outside_fences(text, lambda chunk: ROLE_RE.sub(repl, chunk))


def convert_directives(text):
    """
    Convert ".. deprecated:: X"-style directives to bold lead-ins. Left alone
    they render as a paragraph literally beginning with ".. deprecated::".
    """
    def convert(chunk):
        lines = chunk.splitlines(keepends=True)
        out = []
        index = 0
        while index < len(lines):
            match = DIRECTIVE_RE.match(lines[index].rstrip("\n"))
            if not match:
                out.append(lines[index])
                index += 1
                continue

            indent, name, arg = match.group(1), match.group(2).lower(), match.group(3).strip()
            index += 1

            body_lines, index = take_indented_body(lines, index, len(indent.expandtabs()))
            body = " ".join(line.strip() for line in body_lines if line.strip())

            if name in VERSIONED:
                lead = f"{VERSIONED[name]} {arg}" if arg else VERSIONED[name]
            else:
                lead = ADMONITIONS.get(name, name.replace("_", " ").replace("-", " ").capitalize())
                body = " ".join(part for part in (arg, body) if part)

            out.append(f"{indent}**{lead}:**" + (f" {body}" if body else "") + "\n")
            out.append("\n")
        return "".join(out)

    return map_outside_fences(text, convert)


def take_indented_body(lines, start, base_indent):
    """
    Collect the lines indented deeper than base_indent, plus the index of the
    first line that is not part of the block. Trailing blanks are not consumed.
    """
    body = []
    index = start
    last_content = start
    while index < len(lines):
        line = lines[index].rstrip("\n")
        if not line.strip():
            body.append(lines[index])
            index += 1
            continue
        if indent_width(line) <= base_indent:
            break
        body.append(lines[index])
        index += 1
        last_content = index
    return body[:last_content - start], last_content


def take_flat_body(lines, start):
    """Collect a literal block whose indentation was destroyed upstream."""
    body = []
    index = start
    last_content = start
    blank_run = 0
    while index < len(lines):
        raw = lines[index].rstrip("\n")
        if not raw.strip():
            blank_run += 1
            # Two consecutive blank lines end a flattened block.
            if blank_run >= 2:
                break
            body.append(lines[index])
            index += 1
            continue
        if any(pattern.match(raw) for pattern in FLAT_TERMINATORS):
            break
        blank_run = 0
        body.append(lines[index])
        index += 1
        last_content = index
    return body[:last_content - start], last_content


def looks_like_code(block):
    """Whether a block under an "Example:" lead-in is code rather than prose."""
    source = textwrap.dedent(block)
    if CODE_SHAPE_RE.search(source):
        return True
    if not PYTHONISH_RE.search(source):
        return False
    try:
        ast.parse(source)
    except SyntaxError:
        return False
    return True


def fence_language(block):
    """
    Pick "python" or "text". A block must both parse and look like Python: an
    indented ASCII tree is a valid Python expression statement but is not code.
    """
    source = textwrap.dedent(block)
    if ">>>" in source or CODE_SHAPE_RE.search(source):
        return "python"
    if not PYTHONISH_RE.search(source):
        return "text"
    try:
        ast.parse(source)
    except SyntaxError:
        return "text"
    return "python"


def rewrite_leadin(indent, body, space):
    """
    RST rules for the text before "::": a paragraph that is only "::" disappears,
    one ending in " ::" drops the marker, anything else collapses it to ":".
    """
    if not body.strip():
        return None
    if space or body.rstrip().endswith(":"):
        return f"{indent}{body.rstrip()}"
    return f"{indent}{body.rstrip()}:"


def convert_literal_blocks(text, allow_flat=True):
    """
    Turn RST literal blocks, and "Example:"-style example blocks, into fences.

    The block is normally indented deeper than its lead-in and ends at the first
    non-blank line at or below that indentation. If GoogleProcessor already
    flattened it to column 0 the indentation carries no information, so it ends
    at the first line that is unambiguously markdown again (FLAT_TERMINATORS).
    Pass allow_flat=False to handle only the indented shape.
    """
    def convert(chunk):
        lines = chunk.splitlines(keepends=True)
        out = []
        index = 0
        while index < len(lines):
            raw = lines[index].rstrip("\n")
            match = LITERAL_LEADIN_RE.match(raw)
            example = None
            if not match and not raw.rstrip().endswith("::"):
                example = EXAMPLE_LEADIN_RE.match(raw)
            if not match and not example:
                out.append(lines[index])
                index += 1
                continue

            indent = (match or example).group(1)
            base = len(indent.expandtabs())
            cursor = index + 1

            # Blank lines between the lead-in and the block are not part of it.
            blanks = 0
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
                blanks += 1

            body = []
            if cursor < len(lines):
                if indent_width(lines[cursor].rstrip("\n")) > base:
                    body, cursor = take_indented_body(lines, cursor, base)
                elif allow_flat and blanks and not example:
                    # A column-0 block under an example lead-in cannot be told
                    # apart from prose; only the "::" form justifies the guess.
                    body, cursor = take_flat_body(lines, cursor)

            block = textwrap.dedent("".join(body)).strip("\n") if body else ""

            # "::" marks a literal block by definition, so it is always fenced.
            # An example lead-in carries no such guarantee, so its block is only
            # fenced when it really is code.
            if example and not looks_like_code(block):
                out.append(lines[index])
                index += 1
                continue

            if not body:
                # No block after all: still drop the stray "::" so it does not
                # render as a trailing double colon.
                lead = rewrite_leadin(indent, match.group(2), match.group(3))
                out.append("" if lead is None else lead + "\n")
                index += 1
                continue

            if example:
                out.append(lines[index])
            else:
                lead = rewrite_leadin(indent, match.group(2), match.group(3))
                if lead is not None:
                    out.append(lead + "\n")

            out.append("\n")
            out.append(f"{indent}```{fence_language(block)}\n")
            out.append(textwrap.indent(block, indent) + "\n")
            out.append(f"{indent}```\n")
            out.append("\n")
            index = cursor
        return "".join(out)

    return map_outside_fences(text, convert)


def convert_rst(text, allow_flat=True):
    """
    Directives first, because ".. deprecated::" ends in "::" and would otherwise
    look like a literal-block lead-in. Then literal blocks, then roles.
    """
    text = convert_directives(text)
    text = convert_literal_blocks(text, allow_flat=allow_flat)
    text = convert_roles(text)
    return text


if HAVE_PYDOC_MARKDOWN:

    @dataclasses.dataclass
    class RstProcessor(Processor):
        """
        Convert RST in docstrings before the Google/Sphinx processors run.
        Registered as "docs_rst_processor.RstProcessor" in pydoc-markdown.yml,
        which imports it by dotted path -- so the repo root must be on
        PYTHONPATH (see .github/workflows/docs.yaml).
        """

        roles: bool = True
        literal_blocks: bool = True
        directives: bool = True

        def process(self, modules, resolver):
            docspec.visit(modules, self._process)

        def _process(self, node):
            if not node.docstring or not node.docstring.content:
                return
            content = node.docstring.content
            if self.directives:
                content = convert_directives(content)
            if self.literal_blocks:
                # Indentation is intact here, so only the indented shape can
                # occur; the flat guess would just risk swallowing prose.
                content = convert_literal_blocks(content, allow_flat=False)
            if self.roles:
                content = convert_roles(content)
            node.docstring.content = content
