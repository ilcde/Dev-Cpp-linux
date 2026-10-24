# Changelog

## 0.2.0 — 2026-10-24

First public development release of the Qt workbench in ilcde's Dev-C++ fork.

- Native Qt UI for Fedora Workstation 44 and Windows 11.
- Compact toolbar with original line icons, restrained dark colors and document tabs.
- Vietnamese default UI and optional English UI.
- C23 and C++26 defaults, selectable older standards and an experimental C++29 option for future toolchains.
- GCC/G++ multi-file builds, library configuration and CMake integration.
- PTY/ConPTY terminals, Git controls and GDB/MI debugging.
- Image/video wallpapers and optional privacy-limited Discord RPC.
- UTF-8 saves, unsaved-change handling and argument-safe process launch.
- English documentation, upstream attribution, platform-separated archives and checksums.
- Windows and Fedora 44 CI with compiler/debugger/terminal tests and packaged GUI startup checks.

The original VCL application remains in the repository. This release is not a complete port of its feature set; see the documented limitations before migrating an existing project.
