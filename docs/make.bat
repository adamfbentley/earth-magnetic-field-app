@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build
set SPHINXOPTS=
set O=-E

if "%1" == "" goto help

if "%1" == "clean" goto clean

%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS% %O%
if errorlevel 1 goto error
goto end

:clean
echo.
echo Removing build artifacts...
rd /s /q %BUILDDIR%
goto end

:help
echo.Please use 'make <target>' where <target> is one of:
echo.  html       to make standalone HTML files
echo.  dirhtml    to make standalone HTML files with a directory for each page
echo.  singlehtml to make a single large HTML file
echo.  pickle     to make pickle files
echo.  json       to make JSON files
echo.  htmlhelp   to make HTML files with Sphinx HTML help builder
echo.  qthelp     to make Qt help files
echo.  devhelp    to make HTML files with a developer help builder
echo.  epub       to make an epub
echo.  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter
echo.  latexpdf   to make PDF files from LaTeX (requires xelatex/pdflatex)
echo.  text       to make text files
echo.  man        to make manual pages
echo.  texinfo    to make Texinfo files
echo.  gettext    to make PO message catalogs
echo.  changes    to make an overview of all changed/added/deleted items
echo.  xml        to make XML files
echo.  pseudoxml  to make pseudoxml files
echo.  linkcheck  to check all external links for integrity
echo.  doctest    to run all doctests embedded in the documentation (if enabled)
echo.  clean      to remove all build artifacts
goto end

:error
echo.
echo Build finished with error(s).

:end
popd
