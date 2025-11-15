[![Linux GCC](https://github.com/sintef-ocean/conan-coinhsl/workflows/Linux%20GCC/badge.svg)](https://github.com/sintef-ocean/conan-coinhsl/actions?query=workflow%3A"Linux+GCC")


[Conan.io](https://conan.io) recipe for [hsl](http://www.hsl.rl.ac.uk/ipopt/).

This recipe is maybe made with the help of `coin-or` builder repository [ThirdParty-HSL](https://github.com/coin-or-tools/ThirdParty-HSL).
If the provided `hsl` archive is from 2023 or newer, the `meson` build system is used instead.

**Note** This recipe does not contain the HSL source code. You need to acquire the sources yourself at [hsl](http://www.hsl.rl.ac.uk/ipopt/). Also make sure that your chosen license permits you to redistribute the compiled binaries before you `conan upload` anything.

## How to use this package

1. Add remote to conan's package [remotes](https://docs.conan.io/2/reference/commands/remote.html)

   ```bash
   $ conan remote add sintef https://package.smd.sintef.no
   ```

2. Using [*conanfile.txt*](https://docs.conan.io/2/reference/conanfile_txt.html) and *cmake* in your project.

   Add *conanfile.txt*:
   ```
   [requires]
   coinhsl/2014.01.10@sintef/stable

   [tool_requires]
   cmake/[>=3.25.0]

   [options]
   coinhsl:hsl_archive=/path/to/your/coinhsl.tar.gz

   [layout]
   cmake_layout

   [generators]
   CMakeDeps
   CMakeToolchain
   VirtualBuildEnv
   ```
   Insert into your *CMakeLists.txt* something like the following lines:
   ```cmake
   cmake_minimum_required(VERSION 3.15)
   project(TheProject CXX)

   find_package(coinhsl REQUIRED)

   add_executable(the_executor code.cpp)
   target_link_libraries(the_executor coinhsl::coinhsl)
   ```
   Install and build e.g. a Release configuration:
   ```bash
   $ conan install . -s build_type=Release -pr:b=default
   $ source build/Release/generators/conanbuild.sh
   $ cmake --preset conan-release
   $ cmake --build build/Release
   $ source build/Release/generators/deactivate_conanbuild.sh
   ```

## Package options

Option | Default | Allowed
---|---|---
shared  | True | [True, False]
fPIC | True | [True, False]
hsl_archive | None | ANY
with_full | True | [True, False]

`hsl_archive` is a file path or url to a `coinhsl.tar.gz` file as explained at [ThirdParty-HSL](https://github.com/coin-or-tools/ThirdParty-HSL). As an alternative, you can specify the environment variable `HSL_ARCHIVE`, and also `HSL_USER` and `HSL_PASSWORD` basic authentication if you store you HSL archive on a password protected webserver.

## Known recipe issues

  - Package developer was unable to compile the library with `flang` version 7.
  - The library has not successfully been compiled on Windows, but it should be possible, see [coinbrew](http://github.com/coin-or/coinbrew).
