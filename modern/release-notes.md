# Dev-C++ Modern 0.2.1

UI and terminal fixes, with original Dev-C++ assets and project compatibility.

- Opaque tool panels and full-width tab strips keep wallpaper out of controls. Consistent close buttons, labeled build actions, Git icons and bordered settings fields.
- Original Dev-C++ icon in the Windows EXE, window/taskbar and Linux launcher.
- Terminal EOF is a normal process exit, with its exit code displayed. Output stays visible when resizing a completed program; closed WinPTY handles are no longer resized.
- Import console .dev source membership and include/library search paths after reviewing compatibility warnings. The original .dev file remains unchanged.
- Create C/C++ console projects from three original templates copied from upstream Templates/.

## Downloads

- Windows 11 x64: extract DevCppModern-0.2.1-windows-x86_64.zip and launch DevCppModern.exe. Keep _internal/ beside it.
- Fedora Workstation 44 x64: extract DevCppModern-0.2.1-fedora44-x86_64.tar.gz and run ./DevCppModern/devcpp-modern. Run install-desktop.sh to register the application icon and launcher.

Python/Qt are bundled; GCC/G++, GDB, Git and CMake must be installed separately. English installation and user guides are included. Checksums accompany both archives.

This is a community fork of Embarcadero/Dev-Cpp, continuing Orwell/Bloodshed Dev-C++. The Qt frontend remains a partial port: Win32 GUI/resource projects, DLL/static-library .dev builds, custom Makefiles and legacy compiler indices need manual CMake/toolchain migration. This is a pre-release, not a claim that the Delphi/VCL runtime has been made cross-platform. Physical GPU/media/Discord combinations are not all covered by CI.
