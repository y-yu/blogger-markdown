PANDOC = pandoc
RM     = rm
CAT    = cat
PBCOPY = pbcopy

.PHONY: clean

docs/%.html: articles/%.md filters/code.py
	$(PANDOC) -f markdown_github+footnotes+header_attributes-hard_line_breaks -t html --mathjax --filter ./filters/code.py $< -o $@
	$(CAT) $@ | $(PBCOPY)

clean:
	$(RM) -rf docs/*.html
