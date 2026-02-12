import re
import os
from pathlib import Path

def sweep_file(path):
    orig_content = path.read_text(encoding='utf-8')
    content = orig_content.replace('\r\n', '\n').strip()
    
    # 1. Normalize block boundaries
    # Temporarily hide image defs at EOF
    parts = re.split(r'\n(?=\[image\d+\]: )', content)
    main_body = parts[0]
    image_defs = parts[1:] if len(parts) > 1 else []
    
    # a. Fix broken bold/italic: match patterns like '*Figure 1 |**' 
    main_body = re.sub(r'^\*+(.*?)\*+$', r'**\1**', main_body, flags=re.M)
    main_body = re.sub(r'(?<!\*)\*(Figure \d+ [|:]+)\*+', r'**\1**', main_body)
    
    # b. Normalize table blocks
    lines = main_body.split('\n')
    new_lines = []
    in_table = False
    for i, line in enumerate(lines):
        clean_line = line.strip()
        is_table_row = clean_line.startswith('|') and clean_line.endswith('|')
        
        if is_table_row:
            if not in_table:
                if new_lines and new_lines[-1] != '':
                    new_lines.append('')
                in_table = True
            new_lines.append(line)
        else:
            if in_table:
                table_start_idx = -1
                for j in range(len(new_lines)-1, -1, -1):
                    if new_lines[j] == '': break
                    table_start_idx = j
                
                rows_in_block = len(new_lines) - table_start_idx
                if rows_in_block >= 1:
                    potential_sep = new_lines[table_start_idx+1] if rows_in_block > 1 else ""
                    if not re.match(r'^\|[:\s-]+\|', potential_sep.strip()):
                        header_cols = new_lines[table_start_idx].count('|') - 1
                        new_sep = '|' + '|'.join(['---'] * header_cols) + '|'
                        new_lines.insert(table_start_idx+1, new_sep)
                
                new_lines.append('')
                in_table = False
            new_lines.append(line)
            
    main_body = '\n'.join(new_lines)
    
    # c. Enforce spacing around headers, lists, images, divs
    # Headers
    main_body = re.sub(r'([^\n])\n(#+ )', r'\1\n\n\2', main_body)
    main_body = re.sub(r'(#+ .*?)\n([^\n])', r'\1\n\n\2', main_body)
    # Lists (escaped hyphen)
    main_body = re.sub(r'([^\n])\n(\s*[\-*+] )', r'\1\n\n\2', main_body)
    main_body = re.sub(r'(\s*[\-*+] .*?)\n([^\n\s\-*+])', r'\1\n\n\2', main_body)
    # Images
    main_body = re.sub(r'([^\n])\n(!\[\]\[)', r'\1\n\n\2', main_body)
    main_body = re.sub(r'(!\[\]\[.*?\])\n([^\n])', r'\1\n\n\2', main_body)
    # Quarto Divs
    main_body = re.sub(r'([^\n])\n(:::)', r'\1\n\n\2', main_body)
    main_body = re.sub(r'(:::)\n([^\n])', r'\1\n\n\2', main_body)
    
    # Normalize multiple newlines
    main_body = re.sub(r'\n{3,}', '\n\n', main_body)
    
    final_content = main_body.strip()
    if image_defs:
        final_content += "\n\n" + "\n".join(image_defs)
    
    path.write_text(final_content + "\n", encoding='utf-8')

def main():
    targets = [Path('index.qmd')]
    targets += list(Path('chapters').glob('*.qmd'))
    
    for t in targets:
        if t.exists():
            sweep_file(t)

if __name__ == '__main__':
    main()
