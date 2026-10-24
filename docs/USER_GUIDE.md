# User guide

## Workspace and files

Open a project directory from **File → Open folder**. The left panel shows its files; double-click a source file to edit it. Tabs can be reordered. A dot marks an unsaved document. Closing a modified file, closing the app or switching workspaces offers Save, Discard and Cancel.

Source files are read as UTF-8. Existing UTF-8 BOM and CRLF line endings are preserved. Saves replace the file atomically. Unsupported encodings are rejected instead of being silently rewritten with replacement characters. Convert legacy ANSI files to UTF-8 before editing them here. Files larger than 8 MiB are not opened by this editor.

The toolbar groups New/Open/Save, Build/Run/Debug/Stop, Terminal and Personalization. Hover an icon to see its label and shortcut. All commands remain available in menus.

## Build and run

**F7** saves modified documents and builds. **F6** builds, then starts the result in a new integrated terminal only when all build steps succeed. Compiler output appears in the Build panel. **Shift+F5** stops the active build/debug session and the last launched program terminal.

By default the active C/C++ file is compiled. Specify `sources` for a multi-file project. See [Project settings](PROJECTS.md). C files are compiled with GCC and C++ files with G++, then linked together. Debug builds use `-g -O0 -Wall -Wextra`.

Opening a folder does not execute its contents. The first build, Git operation or terminal launch asks whether you trust the workspace. Compiler plugins, CMake and Git hooks may execute project code. Trust is scoped to the current workspace session.

## Terminal

Open a shell with **Ctrl+`** or the terminal icon. Linux uses `$SHELL` (or `/bin/bash`); Windows uses PowerShell with ConPTY in source runs and WinPTY in the packaged GUI. Each tab has its own process. Closing a terminal terminates its process group/tree. The terminal supports ANSI colors, cursor movement, resizing and a limited scrollback history.

- `Ctrl+C`: interrupt the program.
- `Ctrl+Shift+C`: copy the selection.
- `Ctrl+Shift+V`: paste clipboard text into the terminal (pasted newlines may execute commands).
- `Shift+PageUp` / `Shift+PageDown`: history.

This is a basic native terminal, not a full replacement for every VS Code terminal feature. Some mouse protocols, key combinations and accessibility features are not implemented.

## Git

Use the Git tab and Refresh to list changes. Select one or more paths to Stage or Unstage. View diff lets you choose staged or unstaged changes. Enter a message and press Commit to commit the staged index. Git identity and authentication come from your normal Git configuration.

The UI never automatically pushes. Use the terminal for `git fetch`, `git pull`, branches and `git push`. Unstage currently uses `git restore --staged`, so it needs an existing HEAD commit. Untracked files do not have a normal Git diff until staged.

## Debugger

Click the editor gutter to toggle a breakpoint, then press **F5**. The IDE builds with symbols and launches GDB/MI. It also adds a temporary breakpoint at `main` so the first stop is useful.

The Debug panel provides Continue, Step over, Step into, Step out and Pause. Local variables and call frames refresh at stops. Double-click a stack frame to navigate to its source. Enter an expression in the evaluation field to ask GDB for its value; expression evaluation can invoke functions or change program state.

Breakpoints are copied into GDB when the session starts. Editing a source clears its stored breakpoint positions; restart debugging after edits. Interactive inferior stdin is not integrated yet—use Run for programs that require input. LLDB, DAP and remote debugging are not implemented.

## Appearance and language

Open Personalization using the sliders icon. Choose Vietnamese or English, a background color, and an optional image or video path. Restart to change the UI language. Increase wallpaper opacity to make the media more visible behind panels; use an empty path to remove it.

Images: PNG, JPEG, WebP and BMP. Video: MP4, WebM, MKV and MOV, depending on available codecs. Videos loop silently and pause while the window is minimized. This changes the IDE background, not the operating system wallpaper. Missing files or decoding failures are reported in the Build log.

## Discord Rich Presence

Create your own application in the [Discord Developer Portal](https://discord.com/developers/applications), copy its Application ID, open Discord desktop and enable RPC in Personalization. No bot token is needed or stored.

The only shared activity text is `C / C++` and `Dev-C++ Modern`. Project names, file contents and filesystem paths are not sent. RPC is off by default. Connection errors appear in the status bar and do not stop the editor. Sandboxed Discord packages may not expose their IPC socket to the IDE.

## Shortcuts

| Command | Shortcut |
| --- | --- |
| New / Open / Save | Ctrl+N / Ctrl+O / Ctrl+S |
| Open folder / Save as | Ctrl+Shift+O / Ctrl+Shift+S |
| Find / Go to line | Ctrl+F / Ctrl+G |
| Build / Run / Debug | F7 / F6 / F5 |
| Stop | Shift+F5 |
| New terminal | Ctrl+` |
