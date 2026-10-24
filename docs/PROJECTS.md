# Projects, standards and libraries

The project file is `devcpp.json` in the workspace root. The settings dialog writes it as UTF-8. Paths are relative to that directory unless absolute. Lists use **one argument per line** in the UI; do not put shell quotes around paths containing spaces.

## Language standards

New projects default to `standard_c: "c23"` and `standard_cpp: "c++26"`. Existing explicit values are retained. The settings dialog offers older standards, GNU dialects and an editable field for compiler-specific choices.

- C23 uses `-std=c23`; [GCC documents its C23 support here](https://gcc.gnu.org/projects/c-status.html).
- C++26 uses `-std=c++26`; [GCC still labels its implementation experimental](https://gcc.gnu.org/projects/cxx-status.html). Support varies by feature and standard library.
- Choose `c++23`, `c++20` or `c++17` when a dependency or older compiler requires it.
- The `c++29` option is for GCC 17 development builds. It is not the default, not a completed standard and not validated by this release's GCC 16 toolchain.

The IDE chooses compiler flags; it cannot add missing compiler/library features. The integration tests compile actual C23 constructs and C++26 pack indexing. Those tests do not establish full language conformance.

Try the ready-to-build examples in `modern/examples/c23` and `modern/examples/cpp26` (or `examples/` in a release archive).

## Configuration reference

| Key | Default | Meaning |
| --- | --- | --- |
| `compiler_c` / `compiler_cpp` | `gcc` / `g++` | Executable name or absolute path; not a shell command |
| `debugger` | `gdb` | GDB executable |
| `sources` | `[]` | Source paths; empty means active editor file |
| `include_dirs` | `[]` | Header search paths, passed with `-I` |
| `library_dirs` | `[]` | Library search paths, passed with `-L` |
| `libraries` | `[]` | Library names, passed with `-l` after object files |
| `compile_flags` | `[]` | Extra compiler arguments, one string per argument |
| `link_flags` | `[]` | Extra linker arguments or archive paths |
| `arguments` | `[]` | Program arguments for Run/Debug |
| `standard_c` / `standard_cpp` | `c23` / `c++26` | Compiler language dialects |
| `executable` | `""` | Output path; default `.devcpp-build/app[.exe]` |
| `cmake` | `false` | Use CMake configure/build instead of the direct compiler pipeline |

Unknown keys and wrong types are rejected. When there is no `devcpp.json`, a `CMakeLists.txt` automatically enables CMake mode. A CMake project must set `executable` before Run or Debug.

## Multi-file example

```json
{
  "sources": ["src/main.cpp", "src/helper.c"],
  "standard_c": "c23",
  "standard_cpp": "c++26",
  "include_dirs": ["vendor/example/include"],
  "library_dirs": ["vendor/example/lib"],
  "libraries": ["example"],
  "compile_flags": ["-DMY_FEATURE=1"],
  "link_flags": [],
  "arguments": ["hello world"]
}
```

C sources are compiled separately from C++ to preserve C linkage. Use `extern "C"` in C++ declarations when calling C functions. Library order matters, especially with static archives. A library name `example` generates `-lexample`; an explicit archive such as `vendor/example/lib/libexample.a` belongs in `link_flags`.

There is no fixed limit on the number of include paths or libraries. Binary compatibility still matters: match OS, architecture, runtime and compiler ABI. Arbitrary MSVC `.lib` files are not guaranteed to work with MinGW. Installing a library is separate from adding its header/linker paths.

## CMake

The IDE runs:

```sh
cmake -S . -B .devcpp-build -DCMAKE_BUILD_TYPE=Debug
cmake --build .devcpp-build --config Debug --parallel
```

Use CMake itself to manage standards, sources, libraries and tools such as Conan/vcpkg. Direct-build fields like `include_dirs` do not override `CMakeLists.txt`.

```cmake
cmake_minimum_required(VERSION 3.30)
project(example LANGUAGES C CXX)
set(CMAKE_C_STANDARD 23)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 26)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(example main.cpp helper.c)
target_include_directories(example PRIVATE vendor/include)
```

Set `executable` to `.devcpp-build/example` on Fedora, or the actual generator-specific `.exe` path on Windows. Use a CMake version that recognizes the requested standard. Package-manager commands can be run in the embedded terminal; there is no GUI package installer yet.
