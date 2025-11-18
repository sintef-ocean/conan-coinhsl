import os
from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import get, unzip, copy, rmdir, rm
from conan.tools.gnu import (
    Autotools, AutotoolsDeps, AutotoolsToolchain,
    PkgConfig, PkgConfigDeps
    )
from conan.tools.meson import Meson, MesonToolchain
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path
from conan.tools.scm import Version
from conan.tools.system.package_manager import Apt

required_conan_version = ">=2.18.0"


class CoinHslConan(ConanFile):
    name = "coinhsl"
    license = ("http://www.hsl.rl.ac.uk/licencing.html",)
    author = "SINTEF Ocean"
    url = "https://github.com/sintef-ocean/conan-coinhsl"
    homepage = "http://www.hsl.rl.ac.uk/ipopt/"
    description =\
        "HSL provides a number of linear solvers that can be used in IPOPT"
    topics = ("Linear solver", "COIN-OR")
    settings = "os", "compiler", "build_type", "arch"
    package_type = "library"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_full": [True, False],
        "hsl_archive": ["ANY"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_full": True,
        "hsl_archive": None
    }

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

        if self.settings.os == "Windows":
            self.options["msys2"].additional_packages = "mingw-w64-ucrt-x86_64-gcc-fortran"

    def requirements(self):
        if self.options.with_full:
            # Not needed for not with_full, e.g. ma27
            self.requires("metis/5.2.1")
            self.requires("openblas/[>=0.3.30]")

    def validate(self):
        if is_msvc(self) and self.info.options.shared:
            raise ConanInvalidConfiguration(f"{self.ref} can not be built as shared with msvc.")

    def build_requirements(self):
        if Version(self.version).major > 2022:
            self.tool_requires("meson/[>=1.2.3 <2]")
        else:
            self.tool_requires("gnu-config/cci.20210814")

            if self._settings_build.os == "Windows":
                self.win_bash = True
                if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                    self.tool_requires("msys2/cci.latest")
            if is_msvc(self):
                self.tool_requires("automake/1.16.5")

        if not self.conf.get("tools.gnu:pkg_config", default=False, check_type=str):
            self.tool_requires("pkgconf/[>=2.2 <3]")

    def layout(self):
        if Version(self.version).major > 2022:
            basic_layout(self, src_folder="coinhsl", build_folder="build")
        else:
            basic_layout(self)

    def source(self):
        if Version(self.version).major < 2023:
            get(self, **self.conan_data["sources"][self.version]["build_scripts"], strip_root=True)

    def generate(self):

        deps = PkgConfigDeps(self)
        deps.generate()

        if Version(self.version).major > 2022:
            tc = MesonToolchain(self)
            tc.generate()
        else:
            at = AutotoolsDeps(self)
            at.generate()

            def yes_no(v): return "yes" if v else "no"

            ac = AutotoolsToolchain(self)
            ac.configure_args.extend([
                f"--enable-shared={yes_no(self.options.shared)}",
                f"--enable-static={yes_no(not self.options.shared)}"
            ])

            if self.options.with_full:
                metis = PkgConfig(self, "metis", pkg_config_path=os.path.join(self.build_folder, "conan"))
                lapack = PkgConfig(self, "openblas", pkg_config_path=os.path.join(self.build_folder, "conan"))

                ac.configure_args.extend([
                    f'--with-lapack-lflags={" ".join(["-L" + " -L".join(lapack.libdirs), "-l" + " -l".join(lapack.libs)])}',
                    f'--with-metis-lflags={" ".join(["-L" + " -L".join(metis.libdirs), "-l" + " -l".join(metis.libs)])}',
                    f'--with-metis-cflags={" ".join(["-I" + " -I".join(metis.includedirs), "-D" + " -D".join(metis.defines)])}',
                ])

            env = ac.environment()

            if is_msvc(self):
                compile_wrapper = unix_path(self, self.conf.get("user.automake:compile-wrapper", check_type=str))
                ar_wrapper = unix_path(self, self.conf.get("user.automake:lib-wrapper", check_type=str))
                env.define("CC", f"{compile_wrapper} cl -nologo")
                env.define("CXX", f"{compile_wrapper} cl -nologo")
                env.define("LD", f"{compile_wrapper} link -nologo")
                env.define("AR", f"{ar_wrapper} lib")
                env.define("NM", "dumpbin -symbols")
                env.define("OBJDUMP", ":")
                env.define("RANLIB", ":")
                env.define("STRIP", ":")
            ac.generate(env)

    def build(self):
        hsl_archive = self.options.hsl_archive
        if not hsl_archive:
            archive_uri = os.environ.get("HSL_ARCHIVE", None)
            self.output.info("Checking environment variable HSL_ARCHIVE")
            if archive_uri is None:
                raise ConanInvalidConfiguration(
                    "option:hsl_archive must point to an hsl archive file," +
                    "url, or environment variable HSL_ARCHIVE must be set")
            hsl_archive = archive_uri

        if hsl_archive is None:
            raise ConanInvalidConfiguration(
                "option:hsl_archive must point to an hsl archive file or url")

        hsl_archive = str(hsl_archive)
        if Version(self.version).major < 2023:
            hsl_destination = os.path.join(self.source_folder, "coinhsl")
        else:
            hsl_destination = self.source_folder
        if hsl_archive.startswith("http"):
            hsl_user = os.environ.get("HSL_USER", None)
            hsl_password = os.environ.get("HSL_PASSWORD", None)
            auth = None
            if hsl_user is not None and hsl_password is not None:
                auth = (hsl_user, hsl_password)
            get(hsl_archive,
                auth=auth,
                strip_root=True,
                destination=hsl_destination)
        else:
            self.output.info("Retrieving HSL from {}".format(hsl_archive))
            unzip(self, hsl_archive, strip_root=True,
                  destination=hsl_destination)

        if Version(self.version).major > 2022:
            meson = Meson(self)
            meson.configure()
            meson.build()
        else:
            autotools = Autotools(self)
            autotools.configure()
            autotools.make(args=["--jobs=1"])  # fails otherwise

    def package(self):
        if Version(self.version).major > 2022:
            meson = Meson(self)
            meson.install()
        else:
            autotools = Autotools(self)
            autotools.install()
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        copy(self, "LICENCE", self.source_folder,
             os.path.join(self.package_folder, "licenses"))

    def package_info(self):
        self.cpp_info.libs = ["coinhsl"]
        if Version(self.version).major < 2023:
            self.cpp_info.includedirs = [os.path.join("include", "coin-or", "hsl")]

        if self.settings.os in ["Linux", "FreeBSD"]:
            # This assumes gfortran, gcc
            self.cpp_info.system_libs.extend(["gfortran", "m"])

    def package_id(self):
        del self.info.options.hsl_archive

    def system_requirements(self):
        if self.settings.compiler == "gcc":
            # Depends on gcc version..
            Apt(self).install(["libgfortran5", "libquadmath0"])
