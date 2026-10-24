"""Project configuration and command construction, independent of Qt."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import tempfile


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".devcpp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
        if path.exists():
            os.chmod(name, path.stat().st_mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@dataclass
class Project:
    compiler_c: str = "gcc"
    compiler_cpp: str = "g++"
    debugger: str = "gdb"
    sources: list[str] = field(default_factory=list)
    include_dirs: list[str] = field(default_factory=list)
    library_dirs: list[str] = field(default_factory=list)
    libraries: list[str] = field(default_factory=list)
    compile_flags: list[str] = field(default_factory=list)
    link_flags: list[str] = field(default_factory=list)
    arguments: list[str] = field(default_factory=list)
    standard_c: str = "c23"
    standard_cpp: str = "c++26"
    executable: str = ""
    cmake: bool = False

    @classmethod
    def load(cls, root: Path) -> Project:
        path = root / "devcpp.json"
        if not path.exists():
            return cls(cmake=(root / "CMakeLists.txt").exists())
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("devcpp.json: expected an object")
        unknown = set(data) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"Unknown settings: {', '.join(sorted(unknown))}")
        defaults = cls()
        for key, value in data.items():
            expected = type(getattr(defaults, key))
            if type(value) is not expected or (expected is list and not all(isinstance(v, str) for v in value)):
                raise ValueError(f"Invalid value: {key}")
            if isinstance(value, str) and "\0" in value:
                raise ValueError(f"Invalid NUL: {key}")
            if isinstance(value, list) and any("\0" in v for v in value):
                raise ValueError(f"Invalid NUL: {key}")
        return cls(**data)

    def save(self, root: Path) -> None:
        atomic_write(root / "devcpp.json", json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n")

    def output(self, root: Path) -> Path:
        return (root / self.executable).resolve() if self.executable else root / ".devcpp-build" / ("app.exe" if os.name == "nt" else "app")

    def build_commands(self, root: Path, active: Path | None) -> list[list[str]]:
        if self.cmake:
            return [["cmake", "-S", str(root), "-B", str(root / ".devcpp-build"), "-DCMAKE_BUILD_TYPE=Debug"],
                    ["cmake", "--build", str(root / ".devcpp-build"), "--config", "Debug", "--parallel"]]
        sources = [(root / s).resolve() for s in self.sources] or ([active] if active else [])
        if not sources:
            raise ValueError("Chọn file C/C++ hoặc khai báo sources trong cấu hình dự án.")
        for source in sources:
            if not source.is_file() or source.suffix.lower() not in (".c", ".cpp", ".cc", ".cxx", ".c++"):
                raise ValueError(f"Invalid source: {source}")
        build_dir = root / ".devcpp-build"
        build_dir.mkdir(exist_ok=True)
        # Relative arguments avoid legacy Windows binutils losing Unicode characters
        # in an otherwise valid workspace path. QProcess sets cwd with Unicode APIs.
        def argument(path):
            try:
                return os.path.relpath(path, root)
            except ValueError:  # different Windows drive
                return str(path)
        objects, commands = [], []
        # Compile C and C++ independently so mixed-language projects retain C linkage.
        for index, source in enumerate(sources):
            c = source.suffix == ".c"
            obj = build_dir / f"source-{index}.o"
            objects.append(argument(obj))
            commands.append([self.compiler_c if c else self.compiler_cpp, "-g", "-O0", "-Wall", "-Wextra",
                             "-std=" + (self.standard_c if c else self.standard_cpp),
                             *["-I" + argument((root / p).resolve()) for p in self.include_dirs],
                             *self.compile_flags, "-c", argument(source), "-o", argument(obj)])
        self.output(root).parent.mkdir(parents=True, exist_ok=True)
        linker = self.compiler_cpp if any(s.suffix != ".c" for s in sources) else self.compiler_c
        commands.append([linker, *objects, *["-L" + argument((root / p).resolve()) for p in self.library_dirs],
                         *["-l" + name for name in self.libraries], *self.link_flags, "-o", argument(self.output(root))])
        return commands


def git_entries(data: str) -> list[tuple[str, str]]:
    """Parse porcelain -z without corrupting spaces, newlines or rename records."""
    records = iter(data.split("\0"))
    result = []
    for record in records:
        if len(record) < 4:
            continue
        status, path = record[:2], record[3:]
        result.append((status, path))
        if "R" in status or "C" in status:
            next(records, None)  # original path follows destination with -z
    return result
