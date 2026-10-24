"""Keep bundled Qt libraries out of the system compiler/debugger environment."""
import os
import sys
from pathlib import Path
from PySide6.QtCore import QProcessEnvironment


def external_environment():
    env = dict(os.environ)
    if getattr(sys, "frozen", False):
        if "LD_LIBRARY_PATH_ORIG" in env:
            env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
        else:
            env.pop("LD_LIBRARY_PATH", None)
        bundle = Path(sys._MEIPASS).resolve()
        env["PATH"] = os.pathsep.join(p for p in env.get("PATH", "").split(os.pathsep)
                                     if p and not Path(p).resolve().is_relative_to(bundle))
    return env


def process_environment():
    result = QProcessEnvironment()
    for key, value in external_environment().items():
        result.insert(key, value)
    return result


def prepare_runtime():
    if os.name == "nt" and getattr(sys, "frozen", False):
        # Import the terminal extension before restoring the process DLL policy.
        import winpty
        import ctypes
        ctypes.windll.kernel32.SetDllDirectoryW(None)
