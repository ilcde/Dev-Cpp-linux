# Qt workbench

This directory contains the native Qt implementation of **Dev-C++ Modern**, maintained in [ilcde/Dev-Cpp-linux](https://github.com/ilcde/Dev-Cpp-linux), a fork of [Embarcadero/Dev-Cpp](https://github.com/Embarcadero/Dev-Cpp).

Start with the [repository README](../README.md). Detailed documentation:

- [Windows 11 setup](../docs/INSTALL_WINDOWS.md)
- [Fedora Workstation 44 setup](../docs/INSTALL_FEDORA.md)
- [User guide](../docs/USER_GUIDE.md)
- [Project configuration and libraries](../docs/PROJECTS.md)
- [Development and packaging](../docs/DEVELOPMENT.md)
- [Troubleshooting](../docs/TROUBLESHOOTING.md)

From the repository root, after creating a virtual environment:

```sh
python -m pip install -e './modern[test,package]'
python -m devcpp.app modern/examples/hello
python -m pytest modern/tests -q
python modern/packaging/build.py
```

Windows checkout launchers: `launch.cmd` and `launch.ps1`. They use a locally extracted toolchain in `.tools/w64devkit/bin` when available. That folder is ignored by Git and is not part of the application release.
