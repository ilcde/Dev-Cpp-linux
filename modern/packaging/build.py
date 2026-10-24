"""Reproducible local packaging without unrelated DLLs leaking in from PATH."""
import os
from pathlib import Path
import subprocess
import sys
import shutil
import importlib.metadata

modern = Path(__file__).resolve().parents[1]
env = dict(os.environ)
if os.name == "nt":
    # Native dependencies from unrelated apps (e.g. ICU from Poppler) can have
    # the same DLL names as Windows system libraries but incompatible exports.
    windows = Path(env.get("SystemRoot", r"C:\Windows"))
    env["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), str(Path(sys.base_prefix)),
                                  str(windows / "System32"), str(windows)])
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
                "--paths", str(modern), "--name", "DevCppModern",
                "--distpath", str(modern / "dist"), "--workpath", str(modern / "build"),
                "--specpath", str(modern / "packaging"), str(modern / "packaging" / "entry.py")],
               env=env, check=True)
for source in [modern.parent / "COPYING.txt", modern.parent / "LICENSE", modern / "README.md"]:
    shutil.copy2(source, modern / "dist" / "DevCppModern" / source.name)
licenses = modern / "dist" / "DevCppModern" / "third-party-licenses"
for name in ["PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "pyte", "wcwidth",
             "pypresence", "pygdbmi", "pywinpty" if os.name == "nt" else "ptyprocess", "pyinstaller"]:
    distribution = importlib.metadata.distribution(name)
    target = licenses / name
    target.mkdir(parents=True, exist_ok=True)
    (target / "METADATA.txt").write_text(str(distribution.metadata), encoding="utf-8")
    for file in distribution.files or []:
        if any(part.lower().startswith(("license", "copying", "notice")) for part in file.parts):
            source = Path(distribution.locate_file(file))
            if source.is_file():
                destination = target / Path(*[part for part in file.parts if part not in ("..", ".")])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
python_license = Path(sys.base_prefix) / ("LICENSE.txt" if os.name == "nt" else "lib/python" + sys.version[:4] + "/LICENSE.txt")
if python_license.is_file():
    shutil.copy2(python_license, licenses / "Python-LICENSE.txt")
