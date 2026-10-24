"""Compatibility with the formats in upstream Source/project.pas and Templates/."""
from configparser import ConfigParser
import csv
from pathlib import Path
from .core import Project

TEMPLATES = Path(__file__).parent / "assets" / "templates"


def read_ini(path):
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = data.decode("utf-16")
    else:
        text = data.decode("utf-8-sig")
    parser = ConfigParser(interpolation=None, strict=False)
    parser.read_string(text)
    return parser


def import_project(path):
    """Import source membership and search paths; never execute legacy commands."""
    ini = read_ini(path)
    options = ini["Project"]
    if options.getint("Type", 1) != 1:
        raise ValueError("Only console .dev projects can be imported. Win32 GUI, DLL and static library projects need a CMake configuration.")
    warnings = []
    sources = []
    count = options.getint("UnitCount", 0)
    if not 0 <= count <= 10000:
        raise ValueError("Invalid UnitCount")
    for index in range(1, count + 1):
        unit = ini[f"Unit{index}"]
        name = unit.get("FileName", "").replace("\\", "/")
        if not unit.getboolean("Compile", True):
            continue
        if Path(name).suffix.lower() not in (".c", ".cc", ".cpp", ".cxx", ".c++"):
            warnings.append(f"Not compiled: {name}")
            continue
        if not (path.parent / name).is_file():
            raise ValueError(f"Source file not found: {name}")
        sources.append(name)
        if unit.getboolean("OverrideBuildCmd", False):
            warnings.append(f"Custom build command not imported: {name}")
        if unit.getboolean("CompileCpp", options.getboolean("IsCpp", False)) != (Path(name).suffix.lower() != ".c"):
            warnings.append(f"Language override not imported: {name}; language follows file extension.")
        if not unit.getboolean("Link", True):
            warnings.append(f"Link exclusion not imported: {name}")
    if not sources:
        raise ValueError("No compilable C/C++ source files in this project")
    for key in ("Compiler", "CppCompiler", "Linker", "CompilerSettings", "ObjFiles", "CommandLine",
                "PrivateResource", "CustomMakefile", "OverrideOutputName", "ExeOutput"):
        if options.get(key, "").strip():
            warnings.append(f"Review {key}: {options[key]}")
    if options.getboolean("UseCustomMakefile", False):
        raise ValueError("Custom Makefile projects need explicit CMake/toolchain configuration; automatic import is unavailable.")
    def paths(key):
        # TStrings.DelimitedText uses comma-separated, quoted entries upstream.
        return [p.strip().replace("\\", "/") for p in next(csv.reader([options.get(key, "")], skipinitialspace=True)) if p.strip()]
    project = Project(sources=sources, include_dirs=paths("Includes"), library_dirs=paths("Libs"))
    warnings.insert(0, "Compiler settings use C23/C++26 defaults. Review toolchain, flags and libraries before building.")
    return project, warnings


def template_catalog():
    return [(path, read_ini(path)["Template"]["Name"]) for path in sorted(TEMPLATES.glob("*.template"))]


def create_project(template, destination, cpp=True):
    ini = read_ini(template)
    unit = ini["Unit0"]
    key = "Cpp" if cpp else "C"
    # Original manifests sometimes differ from filenames only by case.
    source = next(p for p in TEMPLATES.iterdir() if p.name.lower() == unit[key].lower())
    name = unit[key + "Name"]
    if cpp and Path(name).suffix == ".c":
        name = str(Path(name).with_suffix(".cpp"))
    if Path(name).name != name:
        raise ValueError("Invalid template filename")
    content = source.read_text(encoding="utf-8")
    destination.mkdir(parents=False, exist_ok=False)
    (destination / name).write_text(content, encoding="utf-8")
    Project(sources=[name]).save(destination)
    return destination / name
