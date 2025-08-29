.. _getting_started_install:

Installation
============

There are pre-built wheels on PyPI for Python 3.10 to 3.13 for Linux, Windows
and MacOS. Any other Python version is not officially supported::

    pip install icspacket

Alternatively, to build from source, Python development headers, CMake, Ninja
and a compatible compiler must be installed (preferably GCC, MSVC and clang work
too)::

    pip install "git+https://github.com/MatrixEditor/icspacket"



.. tip::

    For development and debugging, there are additional compile time options.
    Take a look at ``pyproject.toml`` or add the following line to the
    ``CMakeLists.txt``::

        add_definitions(-DASN_EMIT_DEBUG=1)

    Be aware that there will be A LOT of textual output if you enable this extra
    logging feature.