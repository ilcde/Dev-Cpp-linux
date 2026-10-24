import os
import sys
from devcpp.runtime import external_environment


def test_packaged_tools_use_system_libraries(monkeypatch, tmp_path):
    bundle = tmp_path / "bundle"
    system = tmp_path / "system-tools"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setenv("PATH", os.pathsep.join([str(bundle / "Qt"), str(system)]))
    monkeypatch.setenv("LD_LIBRARY_PATH", str(bundle))
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/opt/my-library")
    env = external_environment()
    assert env["PATH"] == str(system)
    assert env["LD_LIBRARY_PATH"] == "/opt/my-library"
    assert os.environ["LD_LIBRARY_PATH"] == str(bundle)  # parent Qt remains isolated


def test_packaged_tools_without_original_search_path(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setenv("LD_LIBRARY_PATH", str(tmp_path))
    monkeypatch.delenv("LD_LIBRARY_PATH_ORIG", raising=False)
    assert "LD_LIBRARY_PATH" not in external_environment()
