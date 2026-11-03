#!/usr/bin/env python3
"""Validate relative links and heading anchors in a Markdown repository.

Why this exists
---------------
The vault is documentation-only, so a broken relative link or a stale
``#anchor`` is a functional defect: it dead-ends the reader. External URL
checking is deliberately out of scope because network flakiness would make the
check non-deterministic; this script only validates what the repository itself
controls.

What is checked
---------------
* Inline Markdown links ``[text](target)`` and images ``![alt](target)``
* Reference-style definitions ``[id]: target``
* Relative file targets resolve to an existing file (case-sensitive)
* ``#fragment`` targets resolve to a real heading slug in the target document

What is NOT checked
-------------------
* Remote ``http(s)``, ``mailto:``, and other URI schemes
* Raw HTML ``<a href>`` inside HTML blocks (GitHub's own HTML rendering rules
  are broader than the Markdown parser modelled here)
* Targets inside fenced code blocks and inline code spans

Exit status is 0 when every link resolves, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

# Markdown/HTML surface we deliberately ignore when collecting links.
SKIP_DIRS = {".git", "node_modules", "_site", "vendor", ".jekyll-cache"}
IGNORED_SCHEMES = (
    "http://",
    "https://",
    "//",
    "mailto:",
    "tel:",
    "ftp://",
    "data:",
    "ssh://",
    "git@",
)

FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)*\1", re.DOTALL)

# [text](target "optional title") and ![alt](target)
LINK_RE = re.compile(
    r"(?P<bang>!?)\[(?P<text>[^\]]*)\]"
    r"\(\s*<?(?P<target>[^)\s<>]*)>?(?:\s+(?P<title>\"[^\"]*\"|'[^']*'))?\s*\)"
)
REF_DEF_RE = re.compile(r"^\s{0,3}\[(?P<id>[^\]]+)\]:\s*<?(?P<target>\S+)>?")

ATX_RE = re.compile(r"^\s{0,3}(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*#*\s*$")
SETEXT_RE = re.compile(r"^\s{0,3}(?P<rule>=+|-{2,})\s*$")
HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_code(text: str) -> str:
    """Blank out fenced code blocks and inline code spans, preserving lines."""
    out_lines: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence is None and m:
            fence = m.group("fence")[0] * 3
            out_lines.append("")
            continue
        if fence is not None:
            if line.strip().startswith(fence):
                fence = None
            out_lines.append("")
            continue
        out_lines.append(line)

    joined = "\n".join(out_lines)
    # Drop inline code spans but keep the surrounding text intact.
    cleaned = []
    last = 0
    for m in INLINE_CODE_RE.finditer(joined):
        cleaned.append(joined[last : m.start()])
        cleaned.append(" " * (m.end() - m.start()))
        last = m.end()
    cleaned.append(joined[last:])
    return "".join(cleaned)


def gh_slug(heading: str) -> str:
    """Reproduce GitHub's heading-slug algorithm closely enough to be useful.

    GitHub strips symbols and emoji outright, keeps letters, digits, marks,
    spaces, hyphens, and underscores, lowercases, then turns each space into a
    hyphen. Marks must survive because scripts such as Bengali encode vowel
    signs as separate code points (category Mc), while emoji presentation
    selectors must NOT survive or every emoji heading would gain a stray hyphen.
    """
    text = HTML_TAG_RE.sub("", heading).strip()
    # Variation selectors, zero-width joiner, and combining enclosing keycap
    # accompany emoji and are removed by GitHub along with the pictograph.
    text = text.replace("\ufe0e", "").replace("\ufe0f", "")
    text = text.replace("\u200d", "").replace("\u20e3", "")

    kept = []
    for ch in text.lower():
        if ch.isalnum() or ch in " -_":
            kept.append(ch)
        elif unicodedata.category(ch).startswith("M"):
            kept.append(ch)
        # Everything else (emoji, symbols, punctuation) is dropped like GitHub.
    return "".join(kept).replace(" ", "-")


def headings_and_slugs(text: str) -> set[str]:
    """Return every anchor slug a GitHub-rendered document would expose."""
    body = strip_code(text).splitlines()
    slugs: set[str] = set()
    seen: dict[str, int] = {}
    pending_setext: str | None = None

    for line in body:
        if pending_setext is not None:
            if SETEXT_RE.match(line):
                slugs.update(_register(pending_setext, seen))
                pending_setext = None
                continue
            if line.strip() == "":
                continue
            pending_setext = None

        m = ATX_RE.match(line)
        if m:
            slugs.update(_register(m.group("text"), seen))
            continue

        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "|", ">", "-", "*", "!")):
            pending_setext = stripped
        elif stripped == "":
            pending_setext = None

    return slugs


def _register(heading: str, seen: dict[str, int]) -> set[str]:
    """Register one heading slug, applying GitHub's duplicate suffixing."""
    base = gh_slug(heading)
    if not base:
        return set()
    count = seen.get(base, 0)
    seen[base] = count + 1
    return {base if count == 0 else f"{base}-{count}"}


def collect_links(text: str) -> list[str]:
    """Extract every candidate link target from a Markdown document."""
    body = strip_code(text)
    targets: list[str] = []
    for m in LINK_RE.finditer(body):
        target = (m.group("target") or "").strip()
        if target:
            targets.append(target)
    for line in body.splitlines():
        m = REF_DEF_RE.match(line)
        if m:
            targets.append(m.group("target").strip())
    return targets


def load_allowlist(path: Path) -> list[tuple[str, str]]:
    """Read ``<source path>|<link target>`` pairs, ignoring comments/blanks."""
    entries: list[tuple[str, str]] = []
    if not path.exists():
        return entries
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            raise SystemExit(f"malformed allowlist entry (need 'path|target'): {line}")
        src, target = line.split("|", 1)
        entries.append((src.strip(), target.strip()))
    return entries


def is_ignored(target: str) -> bool:
    lowered = target.lower()
    return any(lowered.startswith(s) for s in IGNORED_SCHEMES)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument("--allowlist", help="file of known-missing path|target pairs")
    parser.add_argument(
        "--github-actions",
        action="store_true",
        help="emit ::error annotations for the Actions log",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    allow = load_allowlist(Path(args.allowlist)) if args.allowlist else []
    allowed_pairs = {(s, t) for s, t in allow}

    files = sorted(
        p
        for p in root.rglob("*.md")
        if not any(part in SKIP_DIRS for part in p.relative_to(root).parts)
    )

    slug_cache: dict[Path, set[str]] = {}
    errors: list[tuple[Path, int, str]] = []
    warnings: list[tuple[Path, str]] = []
    checked = 0

    for md in files:
        raw_lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        text = "\n".join(raw_lines)

        for target in collect_links(text):
            if is_ignored(target):
                continue
            checked += 1

            path_part, _, fragment = target.partition("#")
            path_part = unquote(path_part)
            rel = md.relative_to(root).as_posix()

            if (rel, target) in allowed_pairs or (rel, path_part) in allowed_pairs:
                warnings.append((md, target))
                continue

            if path_part in ("", "."):
                dest = md
            else:
                dest = (md.parent / path_part).resolve()

            if path_part and not dest.exists():
                errors.append((md, _line_of(raw_lines, target), target))
                continue

            if fragment:
                # Compare on the same normal form as headings so combining marks
                # and percent-encoding cannot cause a false failure.
                anchor = unicodedata.normalize("NFC", unquote(fragment)).lower()
                if dest.suffix.lower() == ".md" and dest.is_file():
                    if dest not in slug_cache:
                        slug_cache[dest] = headings_and_slugs(
                            dest.read_text(encoding="utf-8", errors="replace")
                        )
                    slugs = {unicodedata.normalize("NFC", s) for s in slug_cache[dest]}
                    if anchor not in slugs:
                        errors.append(
                            (md, _line_of(raw_lines, target), f"{target} (no such heading)")
                        )

    for md, target in warnings:
        rel = md.relative_to(root).as_posix()
        print(f"::warning file={rel}::allowlisted known-missing link: {target}")
        if not args.github_actions:
            print(f"WARN  {rel}: allowlisted known-missing link -> {target}")

    for md, line_no, target in errors:
        rel = md.relative_to(root).as_posix()
        if args.github_actions:
            print(f"::error file={rel},line={line_no}::broken link: {target}")
        else:
            print(f"FAIL  {rel}:{line_no}: broken link -> {target}")

    print()
    print(f"Scanned {len(files)} Markdown file(s), {checked} internal link(s).")
    print(f"Broken: {len(errors)}  Allowlisted: {len(warnings)}")

    if errors:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


def _line_of(lines: list[str], needle: str) -> int:
    """Best-effort 1-based line number for a link target."""
    for idx, line in enumerate(lines, start=1):
        if needle in line:
            return idx
    return 0


if __name__ == "__main__":
    sys.exit(main())
