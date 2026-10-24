# Dev-C++ Modern 0.2.0

First public development release of ilcde's native Qt workbench, in a fork of [Embarcadero/Dev-Cpp](https://github.com/Embarcadero/Dev-Cpp). The original Delphi/VCL source and attribution remain in the repository.

## Downloads

- **Windows 11 x64:** extract `DevCppModern-0.2.0-windows-x86_64.zip`, then open `DevCppModern.exe`. Keep `_internal/` next to it.
- **Fedora Workstation 44 x64:** extract `DevCppModern-0.2.0-fedora44-x86_64.tar.gz`, then run `./DevCppModern/devcpp-modern`. See `docs/INSTALL_FEDORA.md` for runtime dependencies and the desktop launcher.
- Verify downloads against the attached SHA256 sidecars. Python and Qt are included; install GCC/G++, GDB, Git and CMake separately.

## Included

C23 and C++26 defaults; older dialect choices; compact icon toolbar; Vietnamese and English UI; multi-file GCC/G++ and CMake builds; custom C/C++ library paths; PTY/ConPTY terminal tabs; Git status/diff/stage/commit; GDB breakpoints, stepping, variables and call stacks; image/video backgrounds; optional Discord RPC.

C++26 compiler support is experimental and varies by feature. The C++29 option requires a suitable development compiler and is not validated with the release toolchain.

## Validation and scope

Release artifacts are produced by the Windows/Fedora 44 workflow for the tagged commit. The tests cover actual compiler, GDB, Git, terminal and Qt Build/Run interactions. The Fedora binary is additionally launched under virtual X11 and Wayland display servers.

This is a **pre-release**, not a complete port of the legacy VCL IDE. `.dev` import, clangd completion, integrated debugger stdin and a GUI package installer are not implemented. Desktop GPU behavior, all video codecs and live Discord accounts are not covered by CI. Read the English documentation included in each archive for setup and limitations.
