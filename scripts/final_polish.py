import re
import os
from pathlib import Path

def final_polish(content, filename):
    # 1. Fix Heading Levels
    # Chapters should be #
    # Sections inside should be ## or ###
    
    # Remove redundant chapter titles like ***General Discussion...*** right after #
    if filename.startswith('chap-'):
        content = re.sub(r'^# .*\n+\s*\**.*Chapter \d+.*\**\s*$', r'# Chapter ' + filename.split('-')[1].split('.')[0], content, flags=re.M | re.I)
        
    # 2. Fix the "Part" headers inside Chapter 13 - demote them
    if 'chap-13' in filename:
        content = content.replace('# **Part I:', '## Part I:')
        content = content.replace('# **Part II:', '## Part II:')
        content = content.replace('# **Societal Impact', '## Societal Impact')
        content = content.replace('# Summary', '## Summary')
        content = content.replace('# Acknowledgments', '## Acknowledgments')

    # 3. Cleanup double bolding in headers
    content = re.sub(r'^#+ \*\*(.*?)\*\*$', r'## \1', content, flags=re.M)

    # 4. Table Polish - ensure spacing
    content = re.sub(r'(\n\|.*\|)\n(?![|])', r'\1\n\n', content)
    
    # 5. Spacing
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip() + '\n'

def main():
    root = Path('chapters')
    for f in root.glob('*.qmd'):
        print(f"Polishing {f.name}...")
        txt = f.read_text(encoding='utf-8')
        f.write_text(final_polish(txt, f.name), encoding='utf-8')
        
    idx = Path('index.qmd')
    if idx.exists():
        itxt = idx.read_text(encoding='utf-8')
        # Ensure # Abstract is the only # heading
        itxt = re.sub(r'^# (?!Abstract).*$', r'## \0', itxt, flags=re.M)
        idx.write_text(itxt.strip() + '\n', encoding='utf-8')

if __name__ == "__main__":
    main()
