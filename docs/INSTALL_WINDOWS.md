# Windows 11

## Release executable (x64)

1. Download `DevCppModern-0.2.1-windows-x86_64.zip` and its `.sha256` file from Releases.
2. Compare the hash with `Get-FileHash .\DevCppModern-0.2.1-windows-x86_64.zip -Algorithm SHA256`.
3. Extract the **entire archive** to a writable folder.
4. Run `DevCppModern\DevCppModern.exe`. Keep `_internal/` alongside it.

Python and Qt are bundled. The executable is not code-signed. Do not run the IDE as administrator. The initial folder is the process working directory; choose **File → Open folder** for your project. Use the English UI through **Appearance → Personalize → Language**, then restart.

## Install a toolchain

The application archive does not bundle a compiler. Either use a recent portable [w64devkit](https://github.com/skeeto/w64devkit/releases) or [MSYS2 UCRT64](https://www.msys2.org/). CI tests with w64devkit 2.10.1 (GCC 16.2 and GDB 18.1).

With MSYS2, run this in its **UCRT64** shell:

```sh
pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-gdb \
  mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ninja git
```

Add `C:\msys64\ucrt64\bin` and your Git installation directory to the PATH used to launch the IDE. Alternatively, set absolute paths to `gcc.exe`, `g++.exe` and `gdb.exe` in **Project → Libraries & toolchain**. Git and CMake still need to be available on PATH for their integrations.

Do not combine a 32-bit compiler, 64-bit libraries and a mismatched debugger. Use the same toolchain for compilation and debugging. Old TDM-GCC versions shipped with legacy Dev-C++ do not support the new default standards.

The integrated shell is PowerShell without user profiles. Source runs use ConPTY; the packaged GUI uses the tested WinPTY backend because the bundled ConPTY backend fails to initialize in some windowed processes. Both are real pseudoterminals. `Ctrl+C` interrupts the foreground program; `Ctrl+Shift+C/V` copies/pastes. Build/run starts a separate program terminal so commands are not injected into another program's stdin.

## Run from source

Install Python 3.11 or newer and Git. From PowerShell in the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e './modern[test,package]'
.\.venv\Scripts\devcpp-modern.exe .\modern\examples\hello
```

The checkout's `modern\launch.cmd` can launch the local build and automatically use a toolchain extracted under `modern\.tools\w64devkit\bin`. The downloadable release instead uses the toolchain paths you configure or PATH.

## Updating

Extract a new release into a new folder. Do not overwrite a running executable or merge different `_internal` directories. Project configuration stays in each workspace; appearance preferences are stored separately by Qt under `DevCpp/Modern` in your Windows user settings.
