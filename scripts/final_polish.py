import re
import os
from pathlib import Path

def real_markdown_polish(content):
    # 1. Basic Spacing
    content = content.replace('\r\n', '\n')
    
    # 2. Fix Merged Bold Headers at end of paragraphs
    sections = ['ABSTRACT', 'INTRODUCTION', 'METHODS', 'RESULTS', 'DISCUSSION', 'CONCLUSION', 'SUMMARY', 'BACKGROUND', 'FINDINGS', 'INTERPRETATION', 'ACKNOWLEDGEMENTS', 'GLOSSARY', 'REFERENCES', 'CONTRIBUTIONS', 'RELATED WORK']
    for s in sections:
        content = re.sub(r'([a-z0-9\)\}])\.?\s*\*\*(' + s + r')\*\*', r'\1.\n\n## \2', content)
        content = re.sub(r'([a-z0-9\)\}])\.?\s*\b(' + s + r')\b', r'\1.\n\n## \2', content)

    # 3. Fix Image/Text mashing
    content = re.sub(r'(!\[\]\[image\d+\])([^\n\r])', r'\1\n\n\2', content)
    content = re.sub(r'([^\n\r])(!\[\]\[image\d+\])', r'\1\n\n\2', content)
    content = re.sub(r'(\*\*\*Figure.*?\*)(!\[\]\[image\d+\])', r'\1\n\n\2', content)

    # 4. Spacing around Headers
    content = re.sub(r'([^\n])\n(#+ .*)', r'\1\n\n\2', content)
    content = re.sub(r'(#+ .*)\n([^\n])', r'\1\n\n\2', content)

    # 5. Spacing around Tables
    content = re.sub(r'([^\n])\n(\|.*\|)', r'\1\n\n\2', content)
    content = re.sub(r'(\|.*\|)\n([^\n|])', r'\1\n\n\2', content)

    # 6. Spacing around Lists
    content = re.sub(r'([^\n])\n(\* .)', r'\1\n\n\2', content)
    content = re.sub(r'(\* .)\n([^\n\*])', r'\1\n\n\2', content)
    content = re.sub(r'([^\n])\n(\d+\. .)', r'\1\n\n\2', content)
    content = re.sub(r'(\d+\. .)\n([^\n\d])', r'\1\n\n\2', content)

    # 7. Normalize Headers
    content = re.sub(r'^#+ \*\*(.*?)\*\*$', r'## \1', content, flags=re.M)
    content = re.sub(r'^#+ \*\*\*(.*?)\*\*\*$', r'## \1', content, flags=re.M)
    
    # 8. Clean up artifacts like orphaned bold tags or double spaces
    content = re.sub(r'\*\*\s*\n', '\n', content)
    content = re.sub(r'\n\s*\*\*', '\n', content)
    
    # 9. Triple newlines to double
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 10. Trailing spaces
    content = re.sub(r'[ \t]+\n', '\n', content)

    return content.strip() + '\n'

def main():
    root = Path('chapters')
    for f in root.glob('*.qmd'):
        print(f"Polishing {f.name}...")
        txt = f.read_text(encoding='utf-8')
        f.write_text(real_markdown_polish(txt), encoding='utf-8')
        
    idx = Path('index.qmd')
    if idx.exists():
        print("Polishing index.qmd...")
        itxt = idx.read_text(encoding='utf-8')
        idx.write_text(real_markdown_polish(itxt), encoding='utf-8')

if __name__ == "__main__":
    main()
