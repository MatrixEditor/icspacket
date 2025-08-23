# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys
import pathlib
import setuptools_scm

from caterpillar import options

# Project (Git) root directory
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent

# This option will enable easy documentation of struct classes
options.set_struct_flags(options.S_REPLACE_TYPES)

# Next, we can import out module and all rypes on the struct classes will be
# replaced by their runtime types
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
project = "icspacket"
copyright = "2025, MatrixEditor"
author = "MatrixEditor"
release = setuptools_scm.get_version(str(PROJECT_ROOT))

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_tabs.tabs",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "shibuya"
html_static_path = ["_static"]

html_copy_source = False
html_show_sourcelink = False
