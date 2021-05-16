[![Conan Recipe](https://github.com/sintef-ocean/conan-coinhsl/workflows/Clang%20Conan/badge.svg)](https://github.com/sintef-ocean/conan-coinhsl/actions?query=workflow%3A"Clang+Conan")


[Conan.io](https://conan.io) recipe for [hsl](http://www.hsl.rl.ac.uk/ipopt/).

This recipe is made with the help of `coin-or` builder repository [ThirdParty-HSL](https://github.com/coin-or-tools/ThirdParty-HSL).
The package is usually consumed using the `conan install` command or a *conanfile.txt*.

**Note** This recipe does not contain the HSL source code. You need to acquire the sources yourself at [hsl](http://www.hsl.rl.ac.uk/ipopt/). Also make sure that your chosen license permits you to redistribute the compiled binaries before you `conan upload` anything.

## How to use this package

1. Add remote to conan's package [remotes](https://docs.conan.io/en/latest/reference/commands/misc/remote.html?highlight=remotes):

   ```bash
   $ conan remote add sintef https://conan.sintef.io/public
   ```

2. Using *conanfile.txt* in your project with *cmake*

   Add a [*conanfile.txt*](http://docs.conan.io/en/latest/reference/conanfile_txt.html) to your project. This file describes dependencies and your configuration of choice, e.g.:

   ```
   [requires]
   coinhsl/[>=2014.01.17]@sintef/stable

   [options]
   coinhsl:hsl_archive=/path/to/your/coinhsl.tar.gz

   [imports]
   licenses, * -> ./licenses @ folder=True

   [generators]
   cmake_paths
   cmake_find_package
   ```

   Insert into your *CMakeLists.txt* something like the following lines:
   ```cmake
   cmake_minimum_required(VERSION 3.13)
   project(TheProject CXX)

   include(${CMAKE_BINARY_DIR}/conan_paths.cmake)
   find_package(coinhsl MODULE REQUIRED)

   add_executable(the_executor code.cpp)
   target_link_libraries(the_executor coinhsl::coinhsl)
   ```
   Then, do
   ```bash
   $ mkdir build && cd build
   $ conan install .. -s build_type=<build_type>
   ```
   where `<build_type>` is e.g. `Debug` or `Release`.
   You can now continue with the usual dance with cmake commands for configuration and compilation. For details on how to use conan, please consult [Conan.io docs](http://docs.conan.io/en/latest/)

## Package options

Option | Default | Domain
---|---|---
shared  | True | [True, False]
fPIC | True | [True, False]
hsl_archive | None | ANY

`hsl_archive` is a file path or url to a `coinhsl.tar.gz` file as explained at [ThirdParty-HSL](https://github.com/coin-or-tools/ThirdParty-HSL). As an alternative, you can specify the environment variable `HSL_ARCHIVE`, and also `HSL_USER` and `HSL_PASSWORD` basic authentication if you store you HSL archive on a password protected webserver.

## Known recipe issues

  - Package developer was unable to compile the library with `flang` version 7.
  - The library has not successfully been compiled on Windows, but it should be possible, see [coinbrew](http://github.com/coin-or/coinbrew).
