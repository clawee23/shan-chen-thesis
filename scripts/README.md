# Scripts Directory

## Filter BibTeX entries from Anthology

This script filters out BibTeX entries from the Anthology that are not referenced in the specified Quarto Markdown files.

```shell
python scripts/filter_bib_from_qmds.py \
    latex/references/anthology.bib \
    latex/references/anthology-filtered.bib \
    index.qmd chapters/*.qmd
```
