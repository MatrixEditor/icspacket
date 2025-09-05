.. :layout: compact

.. _icspacket_index:

icspacket
=========

.. rst-class:: lead

    *A collection of Python classes and tools to interact with industrial control
    systems using their protocols.*

.. container:: buttons

    `Getting Started <getting-started/installation.html>`_
    `Examples <getting-started/protocols.html>`_
    `GitHub <https://github.com/MatrixEditor/icspacket>`_




*Contents of this side are WIP*


Getting Started
---------------

There are pre-built wheels on PyPI for Python 3.10 to 3.13 for Linux, Windows
and MacOS. Any other Python version is not officially supported::

    pip install icspacket


.. toctree::
    :caption: Getting Started
    :hidden:

    getting-started/installation
    getting-started/protocols
    getting-started/coreapi

.. toctree::
    :caption: DNP3 / IEEE 1815
    :hidden:

    protocols/dnp3/dnp3read
    protocols/dnp3/dnp3dump
    protocols/dnp3/dnp3resolve
    protocols/dnp3/api

.. toctree::
    :caption: IEC 61850
    :hidden:

    protocols/iec61850/iedmap
    protocols/iec61850/api

.. toctree::
    :caption: MMS / ISO 9506
    :hidden:

    protocols/mms/demo_vars
    protocols/mms/demo_files
    protocols/mms/api


.. toctree::
    :caption: ACSE / X.227
    :hidden:

    protocols/acse/api

.. toctree::
    :caption: COPP / X.226 / ISO 8823
    :hidden:

    protocols/copp/api


.. toctree::
    :caption: COSP / X.225 / ISO 8237-1
    :hidden:

    protocols/cosp/api


.. toctree::
    :caption: COTP / X.224
    :hidden:

    protocols/cotp/api


.. toctree::
    :caption: TPKT Protocol (RFC1006)
    :hidden:

    protocols/tpkt/usage
    protocols/tpkt/api


.. toctree::
    :caption: Development

    changelog