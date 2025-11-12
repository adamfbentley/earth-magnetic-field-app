# Minimal Makefile for Sphinx documentation
# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = MagneticFieldDataAnalyzer
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help Makefile clean

help:
	@echo "Please use `make <target>` where <target> is one of"
	@echo "  html       to make standalone HTML files"
	@echo "  dirhtml    to make standalone HTML files with a directory for each page"
	@echo "  singlehtml to make a single large HTML file"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make JSON files"
	@echo "  htmlhelp   to make HTML files with Sphinx HTML help builder"
	@echo "  qthelp     to make Qt help files"
	@echo "  devhelp    to make HTML files with a developer help builder"
	@echo "  epub       to make an epub" 
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make PDF files from LaTeX (requires xelatex/pdflatex)"
	@echo "  text       to make text files"
	@echo "  man        to make manual pages"
	@echo "  texinfo    to make Texinfo files"
	@echo "  gettext    to make PO message catalogs"
	@echo "  changes    to make an overview of all changed/added/deleted items"
	@echo "  xml        to make XML files"
	@echo "  pseudoxml  to make pseudoxml files"
	@echo "  linkcheck  to check all external links for integrity"
	@echo "  doctest    to run all doctests embedded in the documentation (if enabled)"
	@echo "  clean      to remove all build artifacts"

clean:
	@echo "Removing build artifacts..."
	-rm -rf $(BUILDDIR)/*

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
