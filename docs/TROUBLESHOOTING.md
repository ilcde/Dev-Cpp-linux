# Troubleshooting

## App does not start

Keep the executable, `_internal/` and all other archive contents together. Do not mix versions. On Linux, launch from a terminal to see the loader message. Install the Fedora runtime dependencies from the installation guide.

On Windows, a Qt DLL error often means an incomplete extraction or conflicting DLLs copied into the app directory. Re-extract a clean release. When building locally, use `packaging/build.py`, which collects dependencies with a clean PATH.

Keep `_internal/winpty/winpty-agent.exe` in the extracted Windows bundle: the packaged terminal needs this helper. The release uses WinPTY to avoid a ConPTY initialization failure in windowed frozen applications; this is validated by running a compiled program inside the packaged terminal, not just opening the IDE.

## Fedora Wayland or xcb errors

Launch as the logged-in desktop user, not root. A Wayland session needs valid `WAYLAND_DISPLAY` and `XDG_RUNTIME_DIR`; X11 needs `DISPLAY`. Try `QT_QPA_PLATFORM=xcb` only when XWayland/X11 is available. For xcb plugin errors, ensure `libxkbcommon-x11` and the `xcb-util-*` packages from the installation guide are installed. Headless SSH sessions need a display server; the app is a desktop GUI.

## Compiler / Git / GDB not found

The release bundles the IDE runtime, not development tools. Check `gcc --version`, `g++ --version`, `gdb --version` and `git --version` in the environment that launches the IDE. Restart the IDE after changing PATH. Set absolute compiler/debugger executable paths in project settings when needed; do not enter an entire shell command into those fields.

## Unrecognized C23 / C++26 flag

Upgrade the compiler or select an older dialect in Project settings. A compiler accepting the flag may still lack individual language or library features. See the linked GCC support tables in [Projects](PROJECTS.md). No silent fallback to an older standard is performed.

## Unicode filenames and encoding

The editor supports UTF-8 and Unicode paths. Old compilers and linkers may not. The direct builder uses relative arguments to avoid Windows binutils corrupting Unicode parent-directory names; an individual Unicode filename may still be limited by a particular toolchain. Prefer a current toolchain. Convert legacy ANSI source files to UTF-8 before opening; decoding errors do not overwrite the original.

Windows console output encoding also depends on the program and console code page. A UTF-8 source file alone does not force every C runtime to emit Unicode correctly.

## Build succeeds but Run cannot find the executable

For CMake projects, set `executable` to the actual result path. Multi-configuration generators may place it under `Debug/`. The IDE does not guess which of multiple CMake targets to launch.

## Video background does not play

Check the local path and read the Build panel for decoder errors. Try a WebM video with a widely supported codec. Codec support depends on Qt's multimedia backend and platform libraries. Videos are intentionally silent and pause when the window is minimized. Reduce opacity or disable video if it distracts from editing or uses too much GPU/CPU.

## Discord RPC cannot connect

Use the Application ID, not a bot token. Open the Discord desktop app and enable RPC in Personalization. Sandboxed Discord installs can hide the IPC socket. The editor remains usable without Discord; disable RPC to stop connection attempts.

## Known limits in 0.2.0

- No automatic import of legacy `.dev` projects, DevPak integration or Delphi resource editor.
- No clangd/LSP completion, refactoring, LLDB/DAP or remote debugging.
- Debugger stdin is not integrated; Run supports interactive input through the terminal.
- Breakpoints are synchronized at debug startup; source edits clear local positions.
- Terminal emulation covers common shell use, not every VT/mouse/accessibility feature.
- Git branches, network operations and package-manager installs are available through the terminal, not dedicated GUI dialogs.
- Library ABI/architecture compatibility remains the user's toolchain responsibility.
- The Linux release targets Fedora 44 x86_64, not every Linux distribution or ARM device.

When reporting a bug, include the release version, OS, relevant tool versions, exact steps and non-sensitive output. Avoid posting private source code, credentials or complete environment dumps.
