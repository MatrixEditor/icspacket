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
try:
    import icspacket
except ImportError:
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
autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "shibuya"
html_static_path = ["_static"]

html_copy_source = False
html_show_sourcelink = False
html_baseurl = "https://matrixeditor.github.io/icspacket/"

html_sidebars = {
    "**": [
        "sidebars/localtoc.html",
        "repo-stats-custom.html",
        "sidebars/edit-this-page.html",
    ]
}

html_context = {
    "source_type": "github",
    "source_user": "MatrixEditor",
    "source_repo": "icspacket",
}

html_theme_options = {
    "accent_color": "lime",
    "color_mode": "dark",
    "github_url": "https://github.com/MatrixEditor/icspacket",
    "discussion_url": "https://github.com/MatrixEditor/icspacket/discussions",
    "globaltoc_expand_depth": 2,
    "toctree_maxdepth": 5,
    "nav_links": [
        {
            "title": "Examples",
            "url": "getting-started/protocols",
            "children": [
                {
                    "title": "MMS Utilities",
                    "url": "protocols/mms/examples",
                    "summary": "Manufacturing Message Specification tools",
                },
                {
                    "title": "DNP3 Tools",
                    "url": "protocols/dnp3/examples",
                    "summary": "DNP3 utilities and tools",
                },
                {
                    "title": "IED Enumeration Tool",
                    "url": "protocols/iec61850/iedmap",
                    "summary": "Logical Device enumeration and more",
                }
            ],
        },
    ],
}
