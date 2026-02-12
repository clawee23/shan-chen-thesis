#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('shan-chen-thesis')
CHAPTERS = [
    ROOT / 'chapters' / 'chap-3.qmd',
    ROOT / 'chapters' / 'chap-5.qmd',
    ROOT / 'chapters' / 'chap-6.qmd',
    ROOT / 'chapters' / 'chap-7.qmd',
    ROOT / 'chapters' / 'chap-10.qmd',
]
INDEX_FILE = ROOT / 'index.qmd'
SOURCE_THESIS = Path('source_thesis.md')

TABLE_RE = re.compile(r"^\|.*\|\s*$")
IMAGE_REF_RE = re.compile(r"!\[\]\[(image\d+)\]")
IMAGE_DEF_RE = re.compile(r"^\[(image\d+)\]:\s*<data:image/[^>]+>\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding='utf-8').splitlines()


def write_lines(path: Path, lines: list[str]) -> None:
    text = "\n".join(lines).rstrip("\n") + "\n"
    path.write_text(text, encoding='utf-8')


def is_blank(line: str) -> bool:
    return line.strip() == ""


def normalize_tables(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    in_fence = False

    while i < len(lines):
        line = lines[i]
        if FENCE_RE.match(line):
            in_fence = not in_fence
            out.append(line.rstrip())
            i += 1
            continue

        if not in_fence and TABLE_RE.match(line):
            # Expand block to include table lines with any blank separators.
            j = i
            while j < len(lines):
                if TABLE_RE.match(lines[j]):
                    j += 1
                    continue
                if is_blank(lines[j]):
                    k = j + 1
                    while k < len(lines) and is_blank(lines[k]):
                        k += 1
                    if k < len(lines) and TABLE_RE.match(lines[k]):
                        j = k
                        continue
                break

            block = lines[i:j]
            table_rows = [r.rstrip() for r in block if TABLE_RE.match(r)]

            # Exactly one blank line before table (except BOF).
            while out and is_blank(out[-1]):
                out.pop()
            if out:
                out.append("")

            out.extend(table_rows)

            # Exactly one blank line after table if content follows.
            k = j
            while k < len(lines) and is_blank(lines[k]):
                k += 1
            if k < len(lines):
                out.append("")
            i = k
            continue

        out.append(line.rstrip())
        i += 1

    # Collapse runs of >1 blank lines globally for clean indentation.
    cleaned: list[str] = []
    blank_run = 0
    for l in out:
        if is_blank(l):
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
        else:
            blank_run = 0
            cleaned.append(l)

    return cleaned


def parse_source_image_defs(path: Path) -> dict[str, str]:
    defs: dict[str, str] = {}
    for line in read_lines(path):
        m = IMAGE_DEF_RE.match(line)
        if m:
            defs[m.group(1)] = line.rstrip()
    return defs


def refs_in_lines(lines: list[str]) -> list[str]:
    refs: list[str] = []
    seen = set()
    for line in lines:
        for img in IMAGE_REF_RE.findall(line):
            if img not in seen:
                seen.add(img)
                refs.append(img)
    return refs


def defs_in_lines(lines: list[str]) -> dict[str, tuple[int, str]]:
    defs: dict[str, tuple[int, str]] = {}
    for idx, line in enumerate(lines):
        m = IMAGE_DEF_RE.match(line)
        if m:
            defs[m.group(1)] = (idx, line.rstrip())
    return defs


def ensure_image_defs_at_end(path: Path, source_defs: dict[str, str]) -> tuple[bool, list[str]]:
    lines = read_lines(path)
    refs = refs_in_lines(lines)
    defs_map = defs_in_lines(lines)

    changed = False
    missing_added: list[str] = []

    # Add missing definitions from source_thesis.md where possible.
    for img in refs:
        if img not in defs_map and img in source_defs:
            if lines and not is_blank(lines[-1]):
                lines.append("")
            lines.append(source_defs[img])
            defs_map[img] = (len(lines) - 1, source_defs[img])
            missing_added.append(img)
            changed = True

    if changed:
        defs_map = defs_in_lines(lines)

    # Ensure referenced defs are at file end (definition block).
    refs = refs_in_lines(lines)
    if refs:
        referenced_defs = [(img, defs_map[img][0], defs_map[img][1]) for img in refs if img in defs_map]
        if referenced_defs:
            def_indices = {idx for _, idx, _ in referenced_defs}
            body = [ln for idx, ln in enumerate(lines) if idx not in def_indices]
            while body and is_blank(body[-1]):
                body.pop()
            if body:
                body.append("")
            defs_block = [d for _, _, d in referenced_defs]
            new_lines = body + defs_block
            if new_lines != lines:
                lines = new_lines
                changed = True

    if changed:
        write_lines(path, lines)

    return changed, missing_added


def all_markdown_files(root: Path) -> list[Path]:
    return sorted([p for p in root.rglob('*') if p.suffix in {'.md', '.qmd'}])


def main() -> int:
    source_defs = parse_source_image_defs(SOURCE_THESIS)

    # 1) Normalize table spacing in requested chapters.
    table_changed = []
    for path in CHAPTERS:
        lines = read_lines(path)
        fixed = normalize_tables(lines)
        if fixed != lines:
            write_lines(path, fixed)
            table_changed.append(str(path))

    # 2 & 3) Ensure image defs exist and are at end in every markdown file.
    image_changed = []
    missing = {}
    for path in all_markdown_files(ROOT):
        changed, missing_added = ensure_image_defs_at_end(path, source_defs)
        if changed:
            image_changed.append(str(path))
        if missing_added:
            missing[str(path)] = missing_added

    print('TABLE_FILES_CHANGED')
    for p in table_changed:
        print(p)

    print('IMAGE_FILES_CHANGED')
    for p in image_changed:
        print(p)

    print('MISSING_DEFS_ADDED')
    for p, imgs in missing.items():
        print(f"{p}: {', '.join(imgs)}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
