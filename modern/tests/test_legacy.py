from pathlib import Path
import pytest
from devcpp.legacy import import_project, create_project, template_catalog, TEMPLATES
from devcpp.core import Project


def test_dev_import_retains_sources_paths_and_original(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/main.cpp").write_text("int main() {}")
    data = '[Project]\nType=1\nUnitCount=2\nIsCpp=1\nIncludes="include folder",headers\nLibs=libs\nLinker=-lcustom\n[Unit1]\nFileName=src\\main.cpp\nCompile=1\n[Unit2]\nFileName=ignored.cpp\nCompile=0\n'
    path = tmp_path / "project.dev"
    path.write_text(data)
    original = path.read_bytes()
    project, warnings = import_project(path)
    assert project.sources == ["src/main.cpp"]
    assert project.include_dirs == ["include folder", "headers"]
    assert project.library_dirs == ["libs"]
    assert any("-lcustom" in warning for warning in warnings)
    assert path.read_bytes() == original
    assert not (tmp_path / "devcpp.json").exists()


@pytest.mark.parametrize("setting", ["Type=0", "Type=2", "Type=3", "Type=1\nUseCustomMakefile=1"])
def test_import_rejects_unsupported_build_types(tmp_path, setting):
    (tmp_path / "main.c").write_text("int main(void) {}")
    path = tmp_path / "project.dev"
    path.write_text(f"[Project]\n{setting}\nUnitCount=1\n[Unit1]\nFileName=main.c\n")
    with pytest.raises(ValueError):
        import_project(path)


@pytest.mark.parametrize("cpp", [False, True])
def test_original_templates_create_real_projects_without_overwriting(tmp_path, cpp):
    catalog = template_catalog()
    assert len(catalog) == 3
    for template, title in catalog:
        root = tmp_path / template.stem
        source = create_project(template, root, cpp)
        assert source.suffix == (".cpp" if cpp else ".c")
        assert Project.load(root).sources == [source.name]
        assert "main(" in source.read_text()
        before = source.read_bytes()
        with pytest.raises(FileExistsError):
            create_project(template, root, cpp)
        assert source.read_bytes() == before


def test_bundled_assets_match_upstream_checkout():
    root = Path(__file__).resolve().parents[2]
    for path in TEMPLATES.iterdir():
        assert path.read_text(encoding="utf-8") == (root / "Templates" / path.name).read_text(encoding="utf-8")
    assert (TEMPLATES.parent / "devcpp.ico").read_bytes() == (root / "devcpp.ico").read_bytes()
