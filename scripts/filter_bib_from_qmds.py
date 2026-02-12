#!/usr/bin/env python3
"""
BibTeX Citation Filter for Quarto Markdown Files

This script extracts citations from .qmd files and filters a .bib file to include
only the citations that are actually used in the documents.

Usage:
    python filter_bibtex.py input.bib output.bib file1.qmd [file2.qmd ...]
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Set, List


def is_quarto_crossref(citation: str) -> bool:
    """
    Check if a citation is actually a Quarto cross-reference.
    
    Returns True if the citation starts with common Quarto prefixes:
    - @tbl- (tables)
    - @fig- (figures)
    - @sec- (sections)
    - @alg- (algorithms)
    - @eq-  (equations)
    """
    crossref_prefixes = ['tbl-', 'fig-', 'sec-', 'alg-', 'eq-']
    return any(citation.startswith(prefix) for prefix in crossref_prefixes)


def extract_citations_from_qmd(qmd_file: Path) -> Set[str]:
    """
    Extract all citation keys from a Quarto markdown file.
    
    Handles various citation formats:
    - [@key]
    - [@key1; @key2]
    - [@key, p. 123]
    - [-@key] (suppress author)
    - [see @key]
    - @key (in-text citations)
    
    Excludes Quarto cross-references (@tbl-, @fig-, @sec-, @alg-, @eq-)
    """
    citations = set()
    
    try:
        with open(qmd_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {qmd_file}: {e}")
        return citations
    
    # Find all @mentions first (simplest and most reliable approach)
    # This pattern matches @ followed by valid citation key characters
    all_at_mentions = re.findall(r'@([a-zA-Z0-9_:\-]+)', content)
    
    for mention in all_at_mentions:
        # Skip Quarto cross-references
        if is_quarto_crossref(mention):
            continue
        
        # Skip email-like patterns (contains @ before or after)
        if '@' + mention in re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+', content):
            continue
        
        # Add all other @mentions as potential citations
        # The BibTeX filtering step will handle any false positives
        citations.add(mention)
    
    return citations


def extract_citations_from_multiple_qmd(qmd_files: List[Path]) -> Set[str]:
    """Extract citations from multiple QMD files."""
    all_citations = set()
    excluded_crossrefs = set()
    
    for qmd_file in qmd_files:
        print(f"Processing {qmd_file}...")
        
        # Also track excluded cross-references for informational purposes
        with open(qmd_file, 'r', encoding='utf-8') as f:
            content = f.read()
        all_mentions = re.findall(r'@([a-zA-Z0-9_:-]+)', content)
        crossrefs = {m for m in all_mentions if is_quarto_crossref(m)}
        excluded_crossrefs.update(crossrefs)
        
        citations = extract_citations_from_qmd(qmd_file)
        print(f"  Found {len(citations)} citations (excluded {len(crossrefs)} cross-references)")
        all_citations.update(citations)
    
    if excluded_crossrefs:
        print(f"\nExcluded {len(excluded_crossrefs)} Quarto cross-references total")
        print("  Sample excluded cross-references:")
        for ref in sorted(excluded_crossrefs)[:10]:  # Show first 10 as examples
            print(f"    - @{ref}")
        if len(excluded_crossrefs) > 10:
            print(f"    ... and {len(excluded_crossrefs) - 10} more")
    
    return all_citations


def extract_bibtex_entries(bib_file: Path, used_citations: Set[str]) -> str:
    """
    Extract only the BibTeX entries we need using fast regex parsing.
    This is much faster than full parsing for large files.
    """
    try:
        with open(bib_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading BibTeX file {bib_file}: {e}")
        sys.exit(1)
    
    # Pattern to match complete BibTeX entries
    # Matches: @type{key, ... } with proper brace matching
    entry_pattern = r'@(\w+)\s*\{\s*([^,\s}]+)\s*,'
    
    filtered_entries = []
    found_citations = set()
    
    # Split content into potential entries
    entries = re.split(r'\n(?=@)', content)
    
    for entry_text in entries:
        if not entry_text.strip() or not entry_text.strip().startswith('@'):
            continue
            
        # Extract the key from this entry
        key_match = re.match(entry_pattern, entry_text.strip(), re.MULTILINE)
        if not key_match:
            continue
            
        key = key_match.group(2).strip()
        
        if key in used_citations:
            # Clean up the entry and ensure it's complete
            clean_entry = entry_text.strip()
            if not clean_entry.startswith('@'):
                clean_entry = '@' + clean_entry
                
            filtered_entries.append(clean_entry)
            found_citations.add(key)
    
    missing_citations = used_citations - found_citations
    
    print(f"\nFiltering results:")
    print(f"  Citations found in QMD files: {len(used_citations)}")
    print(f"  Citations found in BibTeX: {len(found_citations)}")
    print(f"  Citations filtered into output: {len(filtered_entries)}")
    
    if missing_citations:
        print(f"  Citations not found in BibTeX: {len(missing_citations)}")
        print("  Missing citations (may be in other .bib files):")
        for citation in sorted(missing_citations):
            print(f"    - {citation}")
    
    return '\n\n'.join(filtered_entries)


def extract_complete_bibtex_entry(content: str) -> str:
    """
    Extract a complete BibTeX entry by properly matching braces.
    This function is now simplified since we split on entry boundaries.
    """
    if not content.strip():
        return ""
    
    lines = content.split('\n')
    entry_lines = []
    brace_count = 0
    started = False
    
    for line in lines:
        if line.strip().startswith('@') and not started:
            started = True
        
        if started:
            entry_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            
            # If we've closed all braces, we're done
            if brace_count == 0 and len(entry_lines) > 1:
                break
    
    return '\n'.join(entry_lines)


def main():
    parser = argparse.ArgumentParser(
        description='Filter BibTeX file based on citations used in Quarto markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python filter_bibtex.py references.bib filtered.bib chapter1.qmd chapter2.qmd
  python filter_bibtex.py main.bib output.bib *.qmd

Note: Quarto cross-references (@tbl-, @fig-, @sec-, @alg-, @eq-) are automatically excluded.
        """
    )
    
    parser.add_argument('input_bib', type=Path,
                       help='Input BibTeX file to filter')
    parser.add_argument('output_bib', type=Path,
                       help='Output BibTeX file with filtered citations')
    parser.add_argument('qmd_files', nargs='+', type=Path,
                       help='One or more Quarto markdown files to scan for citations')
    
    args = parser.parse_args()
    
    # Validate input files
    if not args.input_bib.exists():
        print(f"Error: Input BibTeX file {args.input_bib} does not exist")
        sys.exit(1)
    
    for qmd_file in args.qmd_files:
        if not qmd_file.exists():
            print(f"Error: QMD file {qmd_file} does not exist")
            sys.exit(1)
        if qmd_file.suffix.lower() != '.qmd':
            print(f"Warning: {qmd_file} does not have .qmd extension")
    
    # Extract citations from QMD files
    print("Extracting citations from QMD files...")
    used_citations = extract_citations_from_multiple_qmd(args.qmd_files)
    
    if not used_citations:
        print("No citations found in QMD files!")
        sys.exit(1)
    
    print(f"\nTotal unique citations found: {len(used_citations)}")
    print("Citations:", sorted(used_citations))
    
    # Extract only needed BibTeX entries (fast regex-based approach)
    print(f"\nProcessing BibTeX file: {args.input_bib}")
    filtered_content = extract_bibtex_entries(args.input_bib, used_citations)
    
    # Save filtered BibTeX
    try:
        with open(args.output_bib, 'w', encoding='utf-8') as f:
            f.write(filtered_content)
        print(f"\nFiltered BibTeX saved to: {args.output_bib}")
    except Exception as e:
        print(f"Error writing output file {args.output_bib}: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()