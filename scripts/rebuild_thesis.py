import re
from pathlib import Path

def clean_content(text):
    # Remove triple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove redundant chapter headers inside the file
    lines = text.split('\n')
    # Basic normalization for headings
    new_lines = []
    for line in lines:
        if line.startswith('# '):
            # Normalize to avoid double headers
            line = re.sub(r'# \*\*.*Chapter \d+.*\*\*$', '', line, flags=re.I)
            if not line.strip(): continue
        new_lines.append(line)
    return '\n'.join(new_lines).strip() + '\n'

def extract_section(src_lines, start_idx, end_idx):
    content = "\n".join(src_lines[start_idx:end_idx])
    return content

def main():
    src_path = Path('../source_thesis.md')
    if not src_path.exists():
        print("Source file not found")
        return
        
    lines = src_path.read_text(encoding='utf-8').split('\n')
    
    # Define boundaries (0-indexed line numbers)
    # index.qmd (Abstract only)
    # The Abstract starts around line 27 (Chapter 1 content)
    # Actually, let's put the Outline in chap-1 and Abstract in index.
    
    # Extract Abstract
    abstract_lines = []
    for i in range(27, 201):
        if 'Abstract' in lines[i] or 'CHAPTER 1' in lines[i].upper():
            pass
        abstract_lines.append(lines[i])
        if 'Together, this thesis provides' in lines[i]:
            break
            
    Path('index.qmd').write_text('# Abstract\n\n' + '\n'.join(abstract_lines) + '\n', encoding='utf-8')

    boundaries = [
        ("chapters/chap-1.qmd", 26, 201),
        ("chapters/chap-2.qmd", 201, 299),
        ("chapters/chap-3.qmd", 299, 847),
        ("chapters/chap-4.qmd", 847, 1073),
        ("chapters/chap-5.qmd", 1073, 1706),
        ("chapters/chap-6.qmd", 1706, 2045),
        ("chapters/chap-7.qmd", 2045, 2517),
        ("chapters/chap-8.qmd", 2517, 2822),
        ("chapters/chap-9.qmd", 2822, 2982),
        ("chapters/chap-10.qmd", 2982, 3309),
        ("chapters/chap-11.qmd", 3309, 3444),
        ("chapters/chap-12.qmd", 3444, 3670),
        ("chapters/chap-13.qmd", 3670, 3919),
        ("appendix-temp.md", 3919, 4023)
    ]
    
    image_defs = "\n".join(lines[4023:])
    
    for filename, start, end in boundaries:
        print(f"Generating {filename}...")
        content = extract_section(lines, start, end)
        
        used_images = re.findall(r'!\[\]\[(image\d+)\]', content)
        local_defs = ""
        if used_images:
            for img_id in set(used_images):
                match = re.search(rf'^\[{img_id}\]: .*$', image_defs, re.M)
                if match:
                    local_defs += match.group(0) + "\n"
        
        final_content = content + "\n\n" + local_defs
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(clean_content(final_content), encoding='utf-8')

    # Split Appendices
    app_content = Path("appendix-temp.md").read_text(encoding='utf-8')
    app_lines = app_content.split('\n')
    a_markers = []
    for i, l in enumerate(app_lines):
        if re.match(r'^\*\*A\d+:', l):
            a_markers.append(i)
            
    def save_app(name, start_idx, end_idx):
        content = "\n".join(app_lines[start_idx:end_idx])
        used_images = re.findall(r'!\[\]\[(image\d+)\]', content)
        local_defs = ""
        for img_id in set(used_images):
            match = re.search(rf'^\[{img_id}\]: .*$', image_defs, re.M)
            if match:
                local_defs += match.group(0) + "\n"
        Path(f"chapters/{name}").write_text(clean_content(content + "\n\n" + local_defs), encoding='utf-8')

    save_app("appendix-a.qmd", 0, a_markers[3])
    save_app("appendix-b.qmd", a_markers[3], a_markers[5])
    save_app("appendix-c.qmd", a_markers[5], len(app_lines))
    Path("appendix-temp.md").unlink()

    # Update _quarto.yml
    yml = """project:
  type: book
  output-dir: _output
book:
  title: "From Insights to Impact"
  subtitle: "Utility and Failure Modes of Language Models in Clinical Practice"
  author: "Shan Chen"
  back-to-top-navigation: true
  chapters:
    - index.qmd
    - chapters/chap-1.qmd
    - part: "Part I: Potential Utilities of Language Models in Real Clinical Practice"
      chapters:
        - chapters/chap-2.qmd
        - chapters/chap-3.qmd
        - chapters/chap-4.qmd
        - chapters/chap-5.qmd
        - chapters/chap-6.qmd
    - part: "Part II: Potential Failures of Language Models in Medical Settings"
      chapters:
        - chapters/chap-7.qmd
        - chapters/chap-8.qmd
        - chapters/chap-9.qmd
        - chapters/chap-10.qmd
        - chapters/chap-11.qmd
        - chapters/chap-12.qmd
    - chapters/chap-13.qmd
    - chapters/references.qmd
  appendices:
    - chapters/appendix-a.qmd
    - chapters/appendix-b.qmd
    - chapters/appendix-c.qmd
"""
    Path('_quarto.yml').write_text(yml, encoding='utf-8')

if __name__ == "__main__":
    main()
