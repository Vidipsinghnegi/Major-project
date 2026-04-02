# ============================================================
# Makefile for IEEE LaTeX manuscript
# Usage:
#   make        -> compile paper.pdf (requires pdflatex + bibtex)
#   make clean  -> remove auxiliary files
#   make distclean -> remove all generated files including PDF
# ============================================================

PAPER   = paper
LATEX   = pdflatex
BIBTEX  = bibtex
FLAGS   = -interaction=nonstopmode -halt-on-error

.PHONY: all clean distclean

all: $(PAPER).pdf

$(PAPER).pdf: $(PAPER).tex references.bib \
              sections/introduction.tex \
              sections/design.tex \
              sections/layout.tex \
              sections/simulation.tex \
              sections/results.tex \
              sections/thermal.tex \
              sections/conclusion.tex
	$(LATEX) $(FLAGS) $(PAPER)
	$(BIBTEX) $(PAPER)
	$(LATEX) $(FLAGS) $(PAPER)
	$(LATEX) $(FLAGS) $(PAPER)

clean:
	rm -f $(PAPER).aux $(PAPER).bbl $(PAPER).blg \
	      $(PAPER).log $(PAPER).out $(PAPER).toc \
	      $(PAPER).lof $(PAPER).lot $(PAPER).fls \
	      $(PAPER).fdb_latexmk $(PAPER).synctex.gz \
	      sections/*.aux

distclean: clean
	rm -f $(PAPER).pdf
