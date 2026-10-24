"""Produce platform-separated release archives and SHA256 checksums."""
from pathlib import Path
import hashlib
import shutil
import sys
import tarfile
import tomllib
import zipfile

modern = Path(__file__).resolve().parents[1]
version = tomllib.loads((modern / "pyproject.toml").read_text())["project"]["version"]
platform = sys.argv[1]
if platform not in ("windows-x86_64", "fedora44-x86_64"):
    raise SystemExit("Unsupported release platform")
app = modern / "dist" / "DevCppModern"
if not app.is_dir():
    raise SystemExit("Build the app before bundling")
shutil.copytree(modern.parent / "docs", app / "docs", dirs_exist_ok=True)
shutil.copytree(modern / "examples", app / "examples", dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".devcpp-build", "__pycache__"))
for name in ("LICENSE", "COPYING.txt", "README.md"):
    shutil.copy2(modern.parent / name, app / name)
if platform.startswith("fedora"):
    from PySide6.QtGui import QImage
    image = QImage(str(modern / "devcpp/assets/devcpp.ico"))
    if not image.save(str(app / "devcpp.png")):
        raise SystemExit("Cannot export original Dev-C++ launcher icon")
    for name in ("devcpp-modern", "install-desktop.sh"):
        shutil.copy2(modern / "packaging" / name, app / name)
        (app / name).chmod(0o755)
release = modern / "release"
release.mkdir(exist_ok=True)
stem = f"DevCppModern-{version}-{platform}"
if platform.startswith("windows"):
    output = release / (stem + ".zip")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                archive.write(path, Path("DevCppModern") / path.relative_to(app))
else:
    output = release / (stem + ".tar.gz")
    with tarfile.open(output, "w:gz") as archive:
        archive.add(app, arcname="DevCppModern")
with output.open("rb") as stream:
    digest = hashlib.file_digest(stream, "sha256").hexdigest()
(release / (output.name + ".sha256")).write_text(f"{digest}  {output.name}\n", encoding="ascii")
print(output)
