# Attribution and licensing

## Upstream project

This repository is **ilcde/Dev-Cpp-linux**, a fork of **[Embarcadero/Dev-Cpp](https://github.com/Embarcadero/Dev-Cpp)**. That project continues the work of **Orwell Dev-C++** and **Bloodshed Dev-C++**. The upstream Delphi/VCL sources, resources, translations, notices and history are preserved. The [upstream README](UPSTREAM_README.md) is retained for reference.

The Qt workbench is under `modern/`. It does not imply endorsement by Embarcadero, Orwell or Bloodshed. The application icon is the original root `devcpp.ico`; the bundled console template manifests and source files are unmodified copies from upstream `Templates/`. Their original notices and project license remain applicable. `modern/devcpp/legacy.py` implements compatibility with the project fields read by `Source/project.pas`; it does not reuse the VCL runtime. New line icons in `modern/devcpp/icons.py` are project assets distributed under the same GPL terms.

## Project license

The project is distributed under **GNU GPL version 2 or, at your option, a later version**. Read the root `LICENSE` and `COPYING.txt`. Upstream copyright notices are not removed or replaced. Release source is available from the corresponding Git tag in this repository.

## Qt workbench dependencies

| Component | Use | Upstream / license family |
| --- | --- | --- |
| Python | Application runtime | [python.org](https://www.python.org/), PSF license |
| PySide6 / Shiboken6 / Qt | Native widgets, SVG, multimedia | [Qt for Python](https://doc.qt.io/qtforpython-6/), LGPL/GPL/commercial terms, module dependent |
| pyte | Terminal screen state | [selectel/pyte](https://github.com/selectel/pyte), LGPL |
| pywinpty | Windows ConPTY | [andfoy/pywinpty](https://github.com/andfoy/pywinpty), MIT |
| ptyprocess | Linux PTY process | [pexpect/ptyprocess](https://github.com/pexpect/ptyprocess), ISC |
| pygdbmi | GDB/MI parsing | [cs01/pygdbmi](https://github.com/cs01/pygdbmi), MIT |
| pypresence | Optional Discord IPC | [qwertyquerty/pypresence](https://github.com/qwertyquerty/pypresence), MIT |
| wcwidth | Terminal character widths | [jquast/wcwidth](https://github.com/jquast/wcwidth), MIT |
| PyInstaller | Packaging and bootloader | [pyinstaller.org](https://pyinstaller.org/), GPL with bootloader exception |

Binary packages collect available installed dependency license/notice files under `third-party-licenses/`. Dependency terms are not replaced by the project's GPL notice. Qt libraries remain dynamically linked and can be replaced with compatible builds. See the dependency notices and upstream projects for exact terms and corresponding source.

GCC/G++, GDB, CMake and Git are external executables, not included in the IDE release archives. The Windows CI toolchain comes from [w64devkit 2.10.1](https://github.com/skeeto/w64devkit/releases/tag/v2.10.1); its binaries and corresponding source are supplied by that project, not repackaged here.

Third-party components in the preserved Delphi source retain their original notices; consult the upstream README and files alongside those components.
