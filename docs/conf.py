import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

project = 'Magnetic Field Data Analyzer'
copyright = '2024, Agent-Sprint'
author = 'Agent-Sprint'
release = '1.0.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx.ext.autosummary',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for autodoc ---------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'private-members': False,
    'special-members': '__init__',
    'inherited-members': False,
    'show-inheritance': True,
}

# -- Options for sphinx-autodoc-typehints ----------------------------------
autodoc_typehints = 'signature'

# -- Options for autosummary -----------------------------------------------
autosummary_generate = True

# -- Options for Napoleon (Google/NumPy docstring support) -----------------
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Options for todo extension ----------------------------------------------
todo_include_todos = True
