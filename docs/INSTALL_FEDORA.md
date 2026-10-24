# Fedora Workstation 44

## Release archive (x86_64)

The Linux archive is built inside Fedora 44. It includes Python and Qt; Python installation is not required to run the archive. It is not a universal Linux binary or an AppImage, and older distributions are not supported by this build.

1. Install developer tools and desktop runtime libraries:

```sh
sudo dnf install gcc gcc-c++ gdb git cmake ninja-build \
  libxkbcommon libxkbcommon-x11 mesa-libEGL mesa-libGL mesa-dri-drivers \
  fontconfig dejavu-sans-fonts dejavu-sans-mono-fonts libX11 libXext libxcb \
  xcb-util-cursor xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm \
  dbus-libs libXrender libXi libSM libICE libwayland-client libwayland-cursor libwayland-egl pulseaudio-libs alsa-lib libdrm
```

2. Download the Fedora archive and its `.sha256` file from the same GitHub release. Verify and extract:

```sh
sha256sum -c DevCppModern-0.2.0-fedora44-x86_64.tar.gz.sha256
tar -xzf DevCppModern-0.2.0-fedora44-x86_64.tar.gz
./DevCppModern/devcpp-modern "$HOME/Projects/my-project"
```

The workspace argument is optional. To try the bundled example:

```sh
./DevCppModern/devcpp-modern ./DevCppModern/examples/hello
```

3. Optional: move the extracted folder to a permanent location, then run `./DevCppModern/install-desktop.sh`. This adds a launcher to your user's application menu. It does not require root and does not copy the app elsewhere. Moving the app afterward requires running the installer again. Remove `~/.local/share/applications/devcpp-modern.desktop` to remove the launcher (or the equivalent path under `XDG_DATA_HOME`).

## Wayland and X11

Qt uses the current desktop session. Fedora Workstation normally uses Wayland. For troubleshooting, explicitly select a backend:

```sh
QT_QPA_PLATFORM=wayland ./DevCppModern/devcpp-modern
QT_QPA_PLATFORM=xcb ./DevCppModern/devcpp-modern
```

The `xcb` backend requires a running X server or XWayland. Do not use `sudo` to launch the IDE: it loses your session's display/runtime permissions and changes ownership of files it creates.

CI tests the packaged binary in Fedora 44 under Xvfb (X11) and Weston (headless Wayland). The same job runs real compiler, debugger, Git and Linux PTY tests before producing the archive. Hardware acceleration and video codec behavior still depend on the machine.

## Run from source

Install the dependencies above plus Python:

```sh
sudo dnf install python3 python3-pip
git clone https://github.com/ilcde/Dev-Cpp-linux.git
cd Dev-Cpp-linux
python3 -m venv .venv
.venv/bin/python -m pip install -e './modern[test]'
.venv/bin/devcpp-modern modern/examples/hello
```

Do not install the Python package into the system interpreter with `sudo pip`.

## Compiler check

```sh
gcc --version
g++ --version
gdb --version
git --version
```

Use a recent GCC with `-std=c23` and `-std=c++26` support. The test suite checks C23 `constexpr`/type inference and C++26 pack indexing. An older compiler can still be used by selecting an older dialect in Project settings.
