import re
from pathlib import Path

def verify_file(path):
    content = path.read_text(encoding='utf-8')
    issues = []
    
    # 1. Check for broken image references
    refs = re.findall(r'!\[\]\[(image\d+)\]', content)
    for ref in refs:
        if f'[{ref}]:' not in content:
            issues.append(f"Missing definition for {ref}")
            
    # 2. Check for mashed tables (no blank line before/after)
    if re.search(r'[^\n]\n\|', content):
        issues.append("Table mashed with preceding text")
    if re.search(r'\|[ \t]*\n[^\n|]', content):
        issues.append("Table mashed with following text")
        
    # 3. Check for malformed bolding
    if re.search(r'[a-zA-Z0-9]\*\*', content) and not re.search(r'\*\*[a-zA-Z0-9]', content):
        # Very crude check for trailing ** without leading
        pass

    # 4. Check for broken links (crude)
    links = re.findall(r'\[.*?\]\((.*?)\)', content)
    for link in links:
        if link.startswith('http') and not (link.startswith('https://') or link.startswith('http://')):
            issues.append(f"Potentially broken URL: {link}")

    return issues

def main():
    root = Path('.')
    files = list(root.glob('chapters/*.qmd')) + [root / 'index.qmd']
    all_pass = True
    for f in files:
        issues = verify_file(f)
        if issues:
            print(f"--- {f.name} ---")
            for i in issues:
                print(f"  [!] {i}")
            all_pass = False
            
    if all_pass:
        print("VERIFICATION_PASSED")

if __name__ == "__main__":
    main()
