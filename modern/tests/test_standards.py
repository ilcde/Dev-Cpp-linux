import shutil
import subprocess
from pathlib import Path
import pytest
from devcpp.core import Project


@pytest.mark.parametrize("extension,source", [
    ("c", "#if __STDC_VERSION__ < 202311L\n#error C23 required\n#endif\nconstexpr int answer = 42;\nstatic_assert(answer == 42);\nint main(void) { auto value = answer; return value == 42 ? 0 : 1; }\n"),
    ("cpp", "#if __cplusplus <= 202302L\n#error C++26 required\n#endif\ntemplate<class... T> auto first(T... args) { return args...[0]; }\nint main() { return first(42, 7) == 42 ? 0 : 1; }\n"),
])
def test_current_language_features(tmp_path, extension, source):
    compiler = "gcc" if extension == "c" else "g++"
    if not shutil.which(compiler):
        pytest.skip("Compiler unavailable")
    path = tmp_path / ("main." + extension)
    path.write_text(source)
    project = Project()
    for command in project.build_commands(tmp_path, path):
        result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
    subprocess.run([str(project.output(tmp_path))], check=True, timeout=10)


def test_explicit_older_standard_is_preserved(tmp_path):
    project = Project(standard_c="c17", standard_cpp="c++23")
    project.save(tmp_path)
    assert Project.load(tmp_path) == project
