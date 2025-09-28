# icspacket

A collection of Python classes and tools to interact with industrial control
systems using their protocols. Currently supported protocols are:

```
- DNP3.0 (IEEE 1815)
- MMS (ISO 9506) and mappings for IEC 61850
- ACSE (X.227)
- COPP (X.226)
- COSP (X.225)
- COTP (X.224)
- TPKT (RFC1006)
```

**Please review the documentation for more information and tools: [icspacket-docs](https://matrixeditor.github.io/icspacket/)**

**CI Status**

|Target|Status|
|:----:|------|
|Docs|[![CI: Build and Deploy Docs](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-docs.yml/badge.svg)](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-docs.yml)|
|Linux 3.10-3.13|[![CI: Run Tests on Linux](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-pytest-linux.yml/badge.svg)](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-pytest-linux.yml)|
|Mac 3.10-3.13|[![CI: Run Tests on MacOS](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-pytest-macos.yml/badge.svg)](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-pytest-macos.yml)|
|Windows 3.10-3.13|[![CI: Run Tests on Windows](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-pytest-windows.yml/badge.svg)](https://github.com/MatrixEditor/icspacket/actions/workflows/ci-pytest-windows.yml)|

## Installation

There are pre-built wheels on PyPI for Python 3.10 to 3.13 for Linux, Windows
and MacOS. Any other Python version is not officially supported.

```bash
pip install icspacket
```

Alternatively, to build from source, Python development headers, CMake, Ninja
and a compatible compiler must be installed (preferably GCC, MSVC and clang work
too).

```bash
pip install git+https://github.com/MatrixEditor/icspacket
```

## Disclaimer

This project is shared openly to help the community explore, learn, and advance
research on industrial control systems, networking protocols, and related
technologies. Our goal is to provide a resource that encourages experimentation,
collaboration, and education.

The material in this repository is **for research and learning only**. It is not
intended for direct use in production systems or commercial deployments,
especially within live industrial environments where safety and reliability are
critical.

If you decide to build on this work, we encourage you to adopt secure coding
practices, apply a structured security development process, and consider how
you’ll generate and track indicators of compromise in line with your specific
goals.

## License

Distributed under the GNU General Public License (V3). See [License](LICENSE) for more information.