.PHONY: clean-latex

help:
	@echo "Available targets:"
	@echo "  pdf:              Generate PDF version of the thesis."
	@echo "  web:              Generate web version of the thesis."
	@echo "  clean-latex:      Clean up LaTeX auxiliary files."
	@echo "  update-anthology: Update the filtered Anthology bibliography based on the chapter references."

pdf:
	make clean-latex
	make update-anthology
	quarto preview --render pdf
	
web:
	make update-anthology
	quarto preview --render html

clean-latex:
	find latex/ -type f \( -name "*.fls" -o -name "*.aux" -o -name "*.fdb_latexmk" -o -name "*.log" -o -name "*.synctex.gz" -o -name "*.toc" \) -delete
	find . -type f \( -name "*.fls" -o -name "*.aux" -o -name "*.fdb_latexmk" -o -name "*.log" -o -name "*.synctex.gz" -o -name "*.toc" -o -name "*.out" \) -delete
	rm -rf _output/ .quarto/


update-anthology:
	python scripts/filter_bib_from_qmds.py \
		latex/references/anthology.bib \
		latex/references/anthology-filtered.bib \
		index.qmd chapters/*.qmd tables/chap-8-divemt/_languages-small.qmd