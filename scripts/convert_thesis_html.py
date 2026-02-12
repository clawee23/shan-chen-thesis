#!/usr/bin/env python3
"""Convert thesis HTML into Quarto chapter and appendix files."""

from __future__ import annotations

import argparse
import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag


@dataclass
class NumberedSection:
    number: int
    start_idx: int
    source_title: str
    blocks: list[Tag]


@dataclass
class AppendixSection:
    label: str
    start_idx: int
    title: str
    blocks: list[Tag]


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def canonical(text: str) -> str:
    return normalize_ws(text).lower().rstrip(":")


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "section"


def extract_google_redirect(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        q = parse_qs(parsed.query).get("q")
        if q:
            return q[0]
    return url


def parse_class_styles(soup: BeautifulSoup) -> dict[str, dict[str, bool]]:
    style_map: dict[str, dict[str, bool]] = {}
    css = "\n".join(tag.get_text("\n") for tag in soup.find_all("style"))
    for class_name, body in re.findall(r"\.([a-zA-Z0-9_-]+)\s*\{([^}]*)\}", css):
        lower = body.lower()
        style_map[class_name] = {
            "bold": "font-weight:700" in lower or "font-weight: 700" in lower,
            "italic": "font-style:italic" in lower or "font-style: italic" in lower,
            "underline": "text-decoration:underline" in lower or "text-decoration: underline" in lower,
        }
    return style_map


def format_inline(text: str, *, bold: bool = False, italic: bool = False, underline: bool = False) -> str:
    if not text:
        return ""
    rendered = html.unescape(text)
    if underline:
        rendered = f"<u>{rendered}</u>"
    if italic:
        rendered = f"*{rendered}*"
    if bold:
        rendered = f"**{rendered}**"
    return rendered


def normalize_image_src(src: str) -> str:
    src = src.strip()
    if src.startswith("images/"):
        return src.replace("images/", "../figures/", 1)
    if src.startswith("/images/"):
        return src.replace("/images/", "../figures/", 1)
    return src


def inline_to_md(
    node: Tag | NavigableString,
    class_styles: dict[str, dict[str, bool]],
    inherited: dict[str, bool] | None = None,
) -> str:
    inherited = inherited or {"bold": False, "italic": False, "underline": False}

    if isinstance(node, NavigableString):
        return format_inline(str(node), **inherited)

    if not isinstance(node, Tag):
        return ""

    current = dict(inherited)
    if node.name in {"strong", "b"}:
        current["bold"] = True
    if node.name in {"em", "i"}:
        current["italic"] = True
    if node.name == "u":
        current["underline"] = True

    for cls in node.get("class", []):
        if cls in class_styles:
            if class_styles[cls].get("bold"):
                current["bold"] = True
            if class_styles[cls].get("italic"):
                current["italic"] = True
            if class_styles[cls].get("underline"):
                current["underline"] = True

    if node.name == "br":
        return "  \n"

    if node.name == "a":
        href = extract_google_redirect(node.get("href", "").strip())
        label = "".join(inline_to_md(c, class_styles, inherited=current) for c in node.children).strip() or href
        return f"[{label}]({href})" if href else label

    if node.name == "img":
        src = normalize_image_src(node.get("src", ""))
        alt = normalize_ws(node.get("alt", ""))
        return f"![{alt}]({src})" if src else ""

    return "".join(inline_to_md(c, class_styles, inherited=current) for c in node.children)


def block_to_md(block: Tag, class_styles: dict[str, dict[str, bool]]) -> str:
    name = block.name.lower()

    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(name[1])
        title = normalize_ws(inline_to_md(block, class_styles))
        return f"{'#' * min(level, 6)} {title}" if title else ""

    if name == "hr":
        return "---"

    if name in {"ul", "ol"}:
        lines = []
        ordered = name == "ol"
        count = 1
        for li in block.find_all("li", recursive=False):
            text = normalize_ws(inline_to_md(li, class_styles))
            if not text:
                continue
            marker = f"{count}." if ordered else "-"
            lines.append(f"{marker} {text}")
            count += 1
        return "\n".join(lines)

    if name in {"p", "td", "th"}:
        text = normalize_ws(inline_to_md(block, class_styles))
        if text:
            return text
        imgs = [inline_to_md(img, class_styles) for img in block.find_all("img")]
        imgs = [i for i in imgs if i]
        return "\n".join(imgs)

    if name == "table":
        return str(block)

    return normalize_ws(inline_to_md(block, class_styles))


def find_candidate_blocks(soup: BeautifulSoup) -> list[Tag]:
    body = soup.body or soup
    target = {"h1", "h2", "h3", "h4", "p", "ul", "ol", "hr", "table"}
    tags: list[Tag] = []
    for el in body.find_all(list(target), recursive=True):
        if not el.parent or el.parent.name == "style":
            continue
        if el.find_parent(list(target)) is not None:
            continue
        tags.append(el)
    return tags


def block_text(block: Tag) -> str:
    return normalize_ws(block.get_text(" ", strip=True))


def exact_chapter_text(n: int) -> str:
    return f"chapter {n}"


def find_heading_chapter_start(blocks: list[Tag], n: int) -> int:
    chapter_label = exact_chapter_text(n)
    heading_idx = None
    for i, block in enumerate(blocks):
        if block.name not in {"h1", "h2", "h3", "h4"}:
            continue
        if canonical(block_text(block)) == chapter_label:
            heading_idx = i
            break
    if heading_idx is None:
        raise RuntimeError(f"Could not find heading for Chapter {n}.")

    start = heading_idx
    for i in range(max(0, heading_idx - 3), heading_idx):
        if canonical(block_text(blocks[i])) == chapter_label:
            start = i
            break
    return start


def find_chapter1_start(blocks: list[Tag], chapter2_start: int) -> tuple[int, str]:
    for i in range(chapter2_start):
        if canonical(block_text(blocks[i])) == "introduction":
            return i, block_text(blocks[i])

    chapter1_candidates = [i for i in range(chapter2_start) if canonical(block_text(blocks[i])) == "chapter 1"]
    if chapter1_candidates:
        return chapter1_candidates[-1], block_text(blocks[chapter1_candidates[-1]])

    raise RuntimeError("Could not determine Chapter 1 start from Introduction/Chapter 1 marker.")


def find_chapter13_start(blocks: list[Tag], chapter12_start: int) -> tuple[int, str]:
    preferred = {"conclusion and future work", "conclusion"}
    for i in range(chapter12_start + 1, len(blocks)):
        txt = canonical(block_text(blocks[i]))
        if txt in preferred:
            return i, block_text(blocks[i])

    for i in range(chapter12_start + 1, len(blocks)):
        if canonical(block_text(blocks[i])) == "chapter 13":
            return i, block_text(blocks[i])

    raise RuntimeError("Could not determine Chapter 13 start from Conclusion/Conclusion and Future Work marker.")


def split_numbered_sections(blocks: list[Tag]) -> list[NumberedSection]:
    starts: dict[int, tuple[int, str]] = {}

    for n in range(2, 13):
        idx = find_heading_chapter_start(blocks, n)
        starts[n] = (idx, block_text(blocks[idx]))

    ch1_idx, ch1_title = find_chapter1_start(blocks, starts[2][0])
    starts[1] = (ch1_idx, ch1_title)

    ch13_idx, ch13_title = find_chapter13_start(blocks, starts[12][0])
    starts[13] = (ch13_idx, ch13_title)

    ordered_starts = sorted((n, idx_title[0], idx_title[1]) for n, idx_title in starts.items())
    numbered_sections: list[NumberedSection] = []
    for i, (number, start_idx, source_title) in enumerate(ordered_starts):
        end_idx = ordered_starts[i + 1][1] if i + 1 < len(ordered_starts) else len(blocks)
        content = blocks[start_idx + 1 : end_idx]
        numbered_sections.append(
            NumberedSection(number=number, start_idx=start_idx, source_title=source_title, blocks=content)
        )

    return numbered_sections


def split_appendices(blocks: list[Tag], after_idx: int) -> list[AppendixSection]:
    appendix_markers: dict[int, tuple[int, str]] = {}
    for i in range(after_idx + 1, len(blocks)):
        txt = block_text(blocks[i])
        m = re.match(r"^A([1-7]):\s*(.+)$", txt)
        if not m:
            continue
        n = int(m.group(1))
        if n not in appendix_markers:
            appendix_markers[n] = (i, txt)

    missing = [n for n in range(1, 8) if n not in appendix_markers]
    if missing:
        raise RuntimeError(f"Missing appendix headings: {', '.join(f'A{n}' for n in missing)}")

    entries = sorted((n, idx, title) for n, (idx, title) in appendix_markers.items())
    sections: list[AppendixSection] = []
    for i, (n, start_idx, title) in enumerate(entries):
        end_idx = entries[i + 1][1] if i + 1 < len(entries) else len(blocks)
        content = blocks[start_idx + 1 : end_idx]
        sections.append(AppendixSection(label=f"A{n}", start_idx=start_idx, title=title, blocks=content))
    return sections


def render_blocks(blocks: list[Tag], class_styles: dict[str, dict[str, bool]]) -> str:
    lines: list[str] = []
    for block in blocks:
        md = block_to_md(block, class_styles)
        if not md:
            continue
        lines.append(md)
        lines.append("")
    text = "\n".join(lines)
    text = re.sub(r"\*\*([^*]+?)\s+\*\*", r"**\1**", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text + "\n" if text else ""


def render_numbered_section(section: NumberedSection, class_styles: dict[str, dict[str, bool]]) -> str:
    lines = [f"# Chapter {section.number}", ""]
    source = section.source_title.strip()
    if source and canonical(source) not in {f"chapter {section.number}", "introduction"}:
        lines.extend([f"## {source}", ""])
    body = render_blocks(section.blocks, class_styles).strip()
    if section.number == 13:
        cut = re.search(r"(^|\n)\*{0,2}A1:\s", body)
        if cut:
            body = body[: cut.start()].rstrip()
    if body:
        lines.append(body)
    return "\n".join(lines).strip() + "\n"


def render_appendix_section(section: AppendixSection, class_styles: dict[str, dict[str, bool]]) -> str:
    lines = [f"# {section.title}", ""]
    body = render_blocks(section.blocks, class_styles).strip()
    if body:
        lines.append(body)
    return "\n".join(lines).strip() + "\n"


def find_abstract_text(blocks: list[Tag], chapter1_start: int, class_styles: dict[str, dict[str, bool]]) -> str:
    for i in range(chapter1_start):
        if canonical(block_text(blocks[i])) == "abstract":
            for j in range(i + 1, chapter1_start):
                if block_text(blocks[j]):
                    body = render_blocks(blocks[j:chapter1_start], class_styles).strip()
                    if body:
                        return "# Abstract\n\n" + body + "\n"
            break
    return (
        "# Abstract\n\n"
        "This thesis was converted from `thesis_content/ShanChenThesis.html`. "
        "Add the final abstract text here if needed.\n"
    )


def cleanup_generated_files(chapters_dir: Path) -> None:
    for path in chapters_dir.glob("chap-*.qmd"):
        path.unlink()
    for path in chapters_dir.glob("appendix-*.qmd"):
        path.unlink()


def write_appendix_groups(
    appendix_sections: list[AppendixSection],
    chapters_dir: Path,
    class_styles: dict[str, dict[str, bool]],
) -> None:
    by_label = {sec.label: sec for sec in appendix_sections}

    groups = {
        "appendix-a.qmd": ["A1", "A2", "A3"],
        "appendix-b.qmd": ["A4", "A5"],
        "appendix-c.qmd": ["A6", "A7"],
    }

    for filename, labels in groups.items():
        parts: list[str] = []
        for label in labels:
            parts.append(render_appendix_section(by_label[label], class_styles).rstrip())
        text = "\n\n".join(parts).strip() + "\n"
        (chapters_dir / filename).write_text(text, encoding="utf-8")


def convert(
    html_path: Path,
    project_dir: Path,
    *,
    dry_run: bool = False,
) -> None:
    chapters_dir = project_dir / "chapters"
    index_qmd = project_dir / "index.qmd"

    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    class_styles = parse_class_styles(soup)
    blocks = find_candidate_blocks(soup)

    numbered_sections = split_numbered_sections(blocks)
    by_number = {sec.number: sec for sec in numbered_sections}
    if set(by_number.keys()) != set(range(1, 14)):
        raise RuntimeError("Expected chapter set 1..13 was not detected.")

    chapter13_marker_idx = None
    for i in range(by_number[12].start_idx + 1, len(blocks)):
        if canonical(block_text(blocks[i])) in {"conclusion and future work", "conclusion", "chapter 13"}:
            chapter13_marker_idx = i
            break
    if chapter13_marker_idx is None:
        raise RuntimeError("Could not determine Chapter 13 marker for appendix splitting.")

    appendix_sections = split_appendices(blocks, chapter13_marker_idx)
    first_appendix_idx = min(sec.start_idx for sec in appendix_sections)
    by_number[13].blocks = blocks[by_number[13].start_idx + 1 : first_appendix_idx]

    if dry_run:
        print("Detected chapters:", ", ".join(f"{n}" for n in sorted(by_number)))
        print("Detected appendices:", ", ".join(sec.label for sec in appendix_sections))
        return

    chapters_dir.mkdir(parents=True, exist_ok=True)
    cleanup_generated_files(chapters_dir)

    for n in range(1, 14):
        out = render_numbered_section(by_number[n], class_styles)
        (chapters_dir / f"chap-{n}.qmd").write_text(out, encoding="utf-8")

    write_appendix_groups(appendix_sections, chapters_dir, class_styles)

    index_qmd.write_text(find_abstract_text(blocks, by_number[1].start_idx, class_styles), encoding="utf-8")

    print("Generated:")
    print(" - index.qmd")
    for n in range(1, 14):
        print(f" - chapters/chap-{n}.qmd")
    print(" - chapters/appendix-a.qmd (A1-A3)")
    print(" - chapters/appendix-b.qmd (A4-A5)")
    print(" - chapters/appendix-c.qmd (A6-A7)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", type=Path, default=Path("thesis_content/ShanChenThesis.html"))
    parser.add_argument("--project", type=Path, default=Path("shan-chen-thesis"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    convert(args.html, args.project, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
