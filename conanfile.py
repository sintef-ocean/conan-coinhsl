from conans import AutoToolsBuildEnvironment, ConanFile, tools
from conans.tools import PkgConfig
from conans.errors import ConanInvalidConfiguration
import os


class CoinHslConan(ConanFile):
    name = "coinhsl"
    version = "2014.01.17"
    license = ("http://www.hsl.rl.ac.uk/licencing.html",)
    author = "SINTEF Ocean"
    url = "https://github.com/sintef-ocean/conan-coinhsl"
    homepage = "http://www.hsl.rl.ac.uk/ipopt/"
    description =\
        "HSL provides a number of linear solvers that can be used in IPOPT"
    topics = ("Linear solver", "COIN-OR")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "hsl_archive": "ANY"
    }
    default_options = {"shared": True, "fPIC": True, "hsl_archive": None}
    generators = "pkg_config"

    _coin_helper = "ThirdParty-HSL"
    _coin_helper_branch = "stable/2.1"
    _autotools = None

    def _configure_autotools(self):
        if self._autotools:
            return self._autotools

        with tools.environment_append({"PKG_CONFIG_PATH": self.build_folder}):
            self._autotools = AutoToolsBuildEnvironment(self)
            self._autotools.libs = []

            # OpenBLAS provides both blas and lapack
            pkg_openblas = PkgConfig("openblas")
            pkg_coinmetis = PkgConfig("coinmetis")
            auto_args = []
            auto_args.append(
                "--with-lapack={}".format(" ".join(pkg_openblas.libs)))
            auto_args.append(
                "--with-metis-lflags={}".format(" ".join(pkg_coinmetis.libs)))
            auto_args.append(
                "--with-metis-cflags={}".format(" ".join(pkg_coinmetis.cflags)))

            self._autotools.configure(args=auto_args)
            return self._autotools

    def configure(self):
        if self.settings.compiler == "Visual Studio":
            raise ConanInvalidConfiguration(
                "This recipe is does not support Visual Studio")

        self.options["openblas"].shared = self.options.shared
        self.options["openblas"].use_thread = True
        self.options["openblas"].build_lapack = True
        self.options["openblas"].dynamic_arch = True

    def build_requirements(self):

        if not self.options.hsl_archive:
            archive_uri = tools.get_env("HSL_ARCHIVE")
            self.output.info("Checking environment variable HSL_ARCHIVE")
            if archive_uri is None:
                raise ConanInvalidConfiguration(
                    "option:hsl_archive must point to an hsl archive file," +
                    "url, or environment variable HSL_ARCHIVE must be set")
            self.options.hsl_archive = archive_uri

    def requirements(self):
        self.requires("coinmetis/4.0.3@sintef/stable")
        self.requires("openblas/[>=0.3.12]")

    def source(self):
        _git = tools.Git()
        _git.clone("https://github.com/coin-or-tools/{}.git"
                   .format(self._coin_helper),
                   branch=self._coin_helper_branch,
                   shallow=True)

        hsl_archive = self.options.hsl_archive

        if hsl_archive is None:
            raise ConanInvalidConfiguration(
                "option:hsl_archive must point to an hsl archive file or url")

        hsl_archive = str(hsl_archive)
        if hsl_archive.startswith("http"):
            hsl_user = tools.get_env("HSL_USER")
            hsl_password = tools.get_env("HSL_PASSWORD")
            auth = None
            if hsl_user is not None and hsl_password is not None:
                auth = (hsl_user, hsl_password)
            tools.get(hsl_archive,
                      auth=auth,
                      strip_root=True,
                      destination="coinhsl")
        else:
            self.output.info("Retrieving HSL from {}".format(hsl_archive))
            tools.untargz(hsl_archive, strip_root=True, destination="coinhsl")

    def build(self):
        # TODO:
        #with self._build_context():
        #    packs = ["mingw-w64-x86_64-gcc-fortran",
        #             "mingw-w64-x86_64-lapack",
        #             "gcc-fortran"]
        #    self.run("pacman -S --noconfirm {}".format(" ".join(packs), win_bash=True))
        autotools = self._configure_autotools()
        autotools.make(args=["--jobs=1"])  # otherwise it fails

    def package(self):
        autotools = self._configure_autotools()
        autotools.install()

        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        os.unlink(os.path.join(self.package_folder, "lib", "libcoinhsl.la"))
        self.copy("LICENCE", src="coinhsl", dst="licenses")

    def package_info(self):
        self.cpp_info.libs = ["coinhsl"]
        self.cpp_info.includedirs = [os.path.join("include", "coin-or", "hsl")]

        # Did not compile with flang, so assume gfortran
        if tools.os_info.is_linux:
            self.cpp_info.system_libs.append("gfortran")
            self.cpp_info.system_libs.append("gomp")  # openMP runtime

    def package_id(self):
        del self.info.options.hsl_archive

    def imports(self):
        self.copy("license*", dst="licenses", folder=True, ignore_case=True)
