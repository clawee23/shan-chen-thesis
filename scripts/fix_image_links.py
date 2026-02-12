import re
import os
from pathlib import Path

def process_file(path, root_dir):
    content = path.read_text(encoding='utf-8')
    
    # 1. Remove all base64 definitions
    # Regex matches [imageN]: <data:image/png;base64,...>
    # Note: the base64 can be very long, so we use a non-greedy match or look for the closing >
    content = re.sub(r'^\[image\d+\]: <data:image/[^>]+>\n?', '', content, flags=re.M)
    
    # 2. Find all images referenced: ![][imageN]
    refs = sorted(list(set(re.findall(r'!\[\]\[(image(\d+))\]', content))))
    
    if refs:
        # Determine relative path to figures/
        if path.parent.name == 'chapters':
            prefix = '../figures/'
        else:
            prefix = 'figures/'
            
        new_defs = []
        for ref_full, num in refs:
            # Check if file exists to be safe
            img_file = f"image{num}.png"
            if os.path.exists(os.path.join(root_dir, 'figures', img_file)):
                new_defs.append(f"[{ref_full}]: {prefix}{img_file}")
            else:
                print(f"Warning: {img_file} not found in figures/ for {path.name}")

        content = content.strip() + "\n\n" + "\n".join(new_defs) + "\n"
    
    path.write_text(content, encoding='utf-8')

def main():
    root = Path('.')
    # Process index.qmd
    process_file(root / 'index.qmd', root)
    # Process all chapters
    for f in (root / 'chapters').glob('*.qmd'):
        process_file(f, root)

if __name__ == '__main__':
    main()
