#!/bin/sh
set -eu
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
desktop_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$desktop_dir"
escaped=$(printf '%s' "$app_dir" | sed 's/\\/\\\\/g; s/"/\\"/g; s/`/\\`/g; s/\$/\\$/g')
cat > "$desktop_dir/devcpp-modern.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Dev-C++ Modern
Comment=C23 and C++ development environment
Exec="$escaped/devcpp-modern"
Icon=applications-development
Terminal=false
Categories=Development;IDE;
EOF
printf 'Installed desktop entry. Keep this application folder at: %s\n' "$app_dir"
