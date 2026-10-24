# Development and releases

## Repository layout

| Path | Purpose |
| --- | --- |
| `Source/`, `Lang/`, original installer files | Preserved upstream Delphi/VCL application |
| `modern/devcpp/app.py` | Window, actions, workspace and integration wiring |
| `modern/devcpp/core.py` | Typed project settings, atomic writes, build commands and Git records |
| `modern/devcpp/jobs.py` | Asynchronous QProcess command pipelines |
| `modern/devcpp/editor.py` | Editor, syntax colors, line gutter and breakpoint markers |
| `modern/devcpp/terminal.py` | pyte rendering with Linux PTY / Windows ConPTY |
| `modern/devcpp/debugger.py` | Tokenized GDB/MI commands and async events |
| `modern/devcpp/appearance.py` | Theme, media wallpaper and optional RPC worker |
| `modern/devcpp/icons.py` | Original SVG path icons rendered by Qt |
| `modern/tests/` | Core, Qt and actual toolchain integration tests |
| `modern/packaging/` | Native executable build, archives and Linux launchers |

The UI uses Qt Widgets, not Qt WebEngine or Electron. Heavy command execution uses QProcess. Terminal reading and Discord IPC run outside the UI thread. Compiler arguments are passed as argument vectors. The direct builder compiles C and C++ independently and links only after all compile steps succeed.

## Development environment

```sh
python -m venv .venv
# Activate the venv, or use its Python executable explicitly.
python -m pip install -e './modern[test,package]'
python -m devcpp.app modern/examples/hello
```

On Windows use `.venv\Scripts\python.exe`; on Fedora use `.venv/bin/python`. Install GCC/G++, GDB and Git on PATH before running the integration tests. Qt needs the runtime dependencies listed in the platform installation guides.

## Tests

```sh
python -m pytest modern/tests -q
```

The suite includes UTF-8/BOM/CRLF saves, cancelled tab closes, argument boundaries, project validation, Git rename records, actual Git stage/commit with Unicode paths, mixed C/C++ compilation and execution, actual GDB breakpoint/step/variable/stack operations, shell interaction, and Build/Run through the Qt window. Dedicated standards tests use C23 `constexpr` and C++26 pack indexing.

Tests without required tools may skip. Release CI installs the tools first; inspect the test reports rather than treating a skipped test as platform validation. Qt tests use `QT_QPA_PLATFORM=offscreen`; packaged Fedora binaries are additionally started under X11 and Wayland.

To capture the actual Qt UI for review:

```sh
python modern/packaging/preview.py
```

This writes a local `modern/preview.png`. The documentation screenshot is a reviewed capture copied into `docs/assets/editor.png`; it is not a mockup.

## Native packaging

```sh
python modern/packaging/build.py
# Windows:
python modern/packaging/bundle.py windows-x86_64
# Fedora 44:
python modern/packaging/bundle.py fedora44-x86_64
```

Build on the target OS. PyInstaller does not cross-compile. The Linux release is built on Fedora 44, and the Windows archive includes an `.exe` and `_internal` directory. Runtime Python and Qt are bundled; developer tools are not.

The Windows build script intentionally removes unrelated directories from PATH during dependency collection. Otherwise similarly named DLLs from third-party software (particularly ICU) can be copied into the package and prevent Qt startup.

Artifacts are written to `modern/release/` with platform-specific filenames and SHA256 sidecars. The archives contain docs, examples and license notices. Do not publish `.venv`, local `.tools`, caches or user settings.

## Release procedure

1. Update the version in `modern/pyproject.toml`, changelog and archive names in documentation.
2. Run local tests and inspect the UI.
3. Push the reviewed commit. The workflow builds Windows and Fedora 44 independently.
4. Require both jobs to succeed, including packaged startup checks. Download the two archive artifacts from that exact workflow run.
5. Create a release tag on that same commit, attach both archives and both SHA256 files, and include tested scope and limitations in the notes.

Version 0.2.0 is published as a pre-release because legacy feature migration is incomplete. Do not label a build as Fedora-tested if its Fedora job failed or was skipped. CI uses a container and virtual display servers; a real GNOME session remains useful for manual graphics, multimedia and accessibility testing.
