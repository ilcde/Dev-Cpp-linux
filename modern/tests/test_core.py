import json
from pathlib import Path
import subprocess
import shutil
import pytest
from devcpp.core import Project, atomic_write, git_entries


def test_unicode_roundtrip_and_atomic_replace(tmp_path):
    path = tmp_path / "tiếng Việt.cpp"
    atomic_write(path, 'printf("Xin chào");\r\n')
    assert path.read_bytes() == 'printf("Xin chào");\r\n'.encode()
    atomic_write(path, "new\n")
    assert path.read_bytes() == b"new\n"
    assert list(tmp_path.glob(".devcpp-*")) == []


def test_project_roundtrip(tmp_path):
    project = Project(include_dirs=["thư viện/include"], libraries=["m"], arguments=["hello world"])
    project.save(tmp_path)
    assert Project.load(tmp_path) == project


@pytest.mark.parametrize("data", [{"sources": "x.c"}, {"cmake": 1}, {"compiler_cpp": ["g++"]}, {"sources": [2]}, {"unknown": True}, [], {"arguments": ["a\0b"]}])
def test_project_rejects_invalid_configuration(tmp_path, data):
    (tmp_path / "devcpp.json").write_text(json.dumps(data))
    with pytest.raises(ValueError):
        Project.load(tmp_path)


def test_mixed_sources_and_library_argument_boundaries(tmp_path):
    for name in ["tiếng Việt.c", "main.cpp"]:
        (tmp_path / name).write_text("", encoding="utf-8")
    project = Project(sources=["tiếng Việt.c", "main.cpp"], include_dirs=["a b"], libraries=["test"], link_flags=["-pthread"])
    commands = project.build_commands(tmp_path, None)
    assert commands[0][0] == "gcc"
    assert commands[1][0] == commands[2][0] == "g++"
    assert "-Ia b" in commands[0]
    assert "tiếng Việt.c" in commands[0]
    assert commands[2].index("-ltest") > commands[2].index(str(Path(".devcpp-build") / "source-1.o"))


def test_git_z_records():
    records = " M file with space.cpp\0R  new name.cpp\0old.cpp\0?? tiếng Việt.c\0 M odd\nname.c\0"
    assert git_entries(records) == [(" M", "file with space.cpp"), ("R ", "new name.cpp"), ("??", "tiếng Việt.c"), (" M", "odd\nname.c")]


def test_cmake_commands(tmp_path):
    project = Project(cmake=True, executable="build/app")
    commands = project.build_commands(tmp_path, None)
    assert commands[0][0] == commands[1][0] == "cmake"
    assert project.output(tmp_path) == tmp_path / "build" / "app"


@pytest.mark.skipif(not shutil.which("gcc") or not shutil.which("g++"), reason="GCC toolchain unavailable")
def test_build_run_mixed_project_with_unicode_path(tmp_path):
    root = tmp_path / "tiếng Việt project"
    root.mkdir()
    (root / "helper.c").write_text("int answer(void) { return 42; }\n")
    (root / "main.cpp").write_text('extern "C" int answer(void);\nint main() { return answer() == 42 ? 0 : 1; }\n')
    project = Project(sources=["helper.c", "main.cpp"])
    for command in project.build_commands(root, None):
        subprocess.run(command, cwd=root, check=True, capture_output=True)
    subprocess.run([str(project.output(root))], cwd=root, check=True, timeout=10)
