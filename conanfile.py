#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import glob
from conans import ConanFile, AutoToolsBuildEnvironment, tools, VisualStudioBuildEnvironment
from conans.errors import ConanInvalidConfiguration


class ncursesConan(ConanFile):
    name = "ncurses"
    version = "6.1"
    url = "https://github.com/conan-community/conan-ncurses"
    homepage = "https://www.gnu.org/software/ncurses"
    author = "Conan Community"
    license = "X11"
    description = "An API, allowing the programmer to write text-based user interfaces, TUIs, " \
                  "in a terminal-independent manner"
    topics = ("conan", "ncurses", "terminal", "screen", "tui")
    settings = "os", "compiler", "arch", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "with_cpp": [True, False],
               "allow_msvc": [True, False], "allow_mingw": [True, False]}
    default_options = {"shared": False, "fPIC": True, "with_cpp": True,
                       "allow_msvc": True, "allow_mingw": True}
    exports = "LICENSE"
    # NOTE: "compile" was patched: .cc files are properly handled with MinGW-style path conversion
    exports_sources = ["ncurses.patch", "compile", "ar-lib"]
    _autotools = None
    _source_subfolder = "source_subfolder"

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    @property
    def _is_mingw_windows(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc" and os.name == "nt"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def requirements(self):
        if self._is_msvc:
            self.requires("getopt/1.0@bincrafters/stable")
            self.requires("dirent-win32/1.23.2@bincrafters/stable")

    def configure(self):
        # FIXME (uilian): Fix Windows support
        if self.settings.os == "Windows" and self.settings.compiler == "gcc" and not self.options.allow_mingw:
            raise ConanInvalidConfiguration("Oops! ncurses is not supported on MinGW yet")
        if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio" and not self.options.allow_msvc:
            raise ConanInvalidConfiguration("Oops! ncurses is not supported for Visual Studio yet")
        if not self.options.with_cpp:
            del self.settings.compiler.libcxx

    def source(self):
        folder_name = "ncurses-%s" % self.version
        sha256 = "aa057eeeb4a14d470101eff4597d5833dcef5965331be3528c08d99cebaa0d17"
        url = "https://invisible-mirror.net/archives/ncurses/%s.tar.gz" % folder_name
        tools.get(url=url, sha256=sha256)
        os.rename(folder_name, self._source_subfolder)

        os.makedirs(os.path.join(self._source_subfolder, 'build-aux'))
        shutil.move('compile', os.path.join(self._source_subfolder, 'build-aux', 'compile'))
        shutil.move('ar-lib', os.path.join(self._source_subfolder, 'build-aux', 'ar-lib'))

    def build_requirements(self):
        if self._is_msvc or self._is_mingw_windows:
            self.build_requires("msys2_installer/latest@bincrafters/stable")

    def _patch_msvc_sources(self):
        if self._is_msvc:
            # TODO: this is a mess! please create patch file from this!
            tools.replace_in_file(os.path.join("include", "MKterm.h.awk.in"),
                                  "#if __MINGW32__",
                                  "#if defined(__MINGW32__) || defined(_MSC_VER)")
            tools.replace_in_file(os.path.join("include", "ncurses_mingw.h"),
                                  "#ifdef __MINGW32__",
                                  "#if defined(__MINGW32__) || defined(_MSC_VER)")
            tools.replace_in_file(os.path.join("include", "nc_termios.h"),
                                  "#if __MINGW32__",
                                  "#if defined(__MINGW32__) || defined(_MSC_VER)")
            tools.replace_in_file(os.path.join("include", "nc_mingw.h"),
                                  "#ifdef __MINGW32__",
                                  "#if defined(__MINGW32__) || defined(_MSC_VER)")
            tools.replace_in_file(os.path.join("ncurses", "base", "lib_driver.c"),
                                  "#ifdef __MINGW32__",
                                  "#if defined(__MINGW32__) || defined(_MSC_VER)")
            tools.replace_in_file(os.path.join("include", "nc_mingw.h"),
                                  "#include <sys/time.h>",
                                  "#if HAVE_SYS_TIME_H\n"
                                  "#include <sys/time.h>\n"
                                  "#endif")
            tools.replace_in_file(os.path.join("progs", "progs.priv.h"),
                                  "/* usually in <unistd.h> */",
                                  "/* usually in <unistd.h> */\n"
                                  "#ifndef STDIN_FILENO\n"
                                  "#define STDIN_FILENO 0\n"
                                  "#endif\n")
            win_driver = os.path.join("ncurses", "win32con", "win_driver.c")
            tools.replace_in_file(win_driver,
                                  "#ifndef __GNUC__",
                                  "#if 0")
            # MSVC cannot check for executable permission https://msdn.microsoft.com/en-us/library/1w06ktdy.aspx
            tools.replace_in_file(os.path.join("ncurses", "curses.priv.h"),
                                  "#define	X_OK\t1",
                                  "#define	X_OK\t0")
            tools.replace_in_file(os.path.join("progs", "progs.priv.h"),
                                  "#define	X_OK\t1",
                                  "#define	X_OK\t0")
            # TODO: below should have #ifdef _MSC_VER for compatibily...
            tools.replace_in_file(win_driver,
                                  "CHAR_INFO ci[n];",
                                  "CHAR_INFO * ci = (CHAR_INFO*) _alloca(sizeof(CHAR_INFO) * n);")
            tools.replace_in_file(win_driver,
                                  "CHAR_INFO ci[limit];",
                                  "CHAR_INFO * ci = (CHAR_INFO*) _alloca(sizeof(CHAR_INFO) * limit);")
            tools.replace_in_file(win_driver,
                                  "CHAR_INFO this_screen[max_cells];",
                                  "CHAR_INFO * this_screen = (CHAR_INFO*) _alloca(sizeof(CHAR_INFO) * max_cells);")
            tools.replace_in_file(win_driver,
                                  "CHAR_INFO that_screen[max_cells];",
                                  "CHAR_INFO * that_screen = (CHAR_INFO*) _alloca(sizeof(CHAR_INFO) * max_cells);")
            tools.replace_in_file(win_driver,
                                  "cchar_t empty[Width];",
                                  "cchar_t * empty = (cchar_t*) _alloca(sizeof(cchar_t) * Width);")
            tools.replace_in_file(win_driver,
                                  "chtype empty[Width];",
                                  "chtype * empty = (chtype*) _alloca(sizeof(chtype) * Width);")
            tools.replace_in_file(os.path.join("ncurses", "win32con", "gettimeofday.c"),
                                  "#include <windows.h>",
                                  "#include <windows.h>\n"
                                  "#include <winsock2.h>")

    def _configure_autotools(self):
        if not self._autotools:
            args = [
                '--enable-overwrite',
                '--without-manpages',
                '--without-tests',
                '--enable-term-driver',
                '--disable-echo',
                '--without-profile',
                '--with-sp-funcs',
                '--enable-pc-files'
                ]

            if self.options.shared:
                args.extend(['--with-shared', '--without-normal', '--without-debug'])
            else:
                if self.settings.build_type == "Debug":
                    args.extend(['--without-shared', '--without-normal', '--with-debug'])
                else:
                    args.extend(['--without-shared', '--with-normal', '--without-debug'])

            if self._is_msvc:
                prefix = tools.unix_path(self.package_folder)
                runtime = str(self.settings.compiler.runtime)
                args.extend(['--prefix=%s' % prefix,
                             '--disable-stripping',  # disable, as /bin/install cannot find strip
                             'ac_cv_func_setvbuf_reversed=no',  # asserts during configure in debug builds
                             'CC=$PWD/build-aux/compile cl -nologo',
                             'CXX=$PWD/build-aux/compile cl -nologo',
                             'CFLAGS=-FS -%s' % runtime,
                             'CXXFLAGS=-FS -%s' % runtime,
                             'CPPFLAGS=-D_WIN32_WINNT=0x0600 -I%s/include' % prefix,
                             'LD=link',
                             'LDFLAGS=user32.lib -L%s/lib' % prefix,
                             'NM=dumpbin -symbols',
                             'STRIP=:',
                             'AR=$PWD/build-aux/ar-lib lib',
                             'RANLIB=:'])

            if self.options.with_cpp:
                args.append('--with-{}'.format("cxx-shared" if self.options.shared else "cxx"))
            else:
                args.extend(['--without-cxx-shared', "--without-cxx"])
            self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
            self._autotools.configure(args=args)
        return self._autotools

    def build(self):
        tools.patch(patch_file="ncurses.patch", base_path=self._source_subfolder)

        with tools.chdir(self._source_subfolder):
            if self._is_msvc:
                self._patch_msvc_sources()

                with tools.vcvars(self.settings):
                    env_build = VisualStudioBuildEnvironment(self)
                    with tools.environment_append(env_build.vars):
                        autotools = self._configure_autotools()
                        autotools.make()
            else:
                autotools = self._configure_autotools()
                autotools.make()

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        with tools.chdir(self._source_subfolder):
            if self._is_msvc:
                with tools.vcvars(self.settings):
                    env_build = VisualStudioBuildEnvironment(self)
                    with tools.environment_append(env_build.vars):
                        autotools = self._configure_autotools()
                        autotools.install()
                with tools.chdir(os.path.join(self.package_folder, "lib")):
                    libs = glob.glob("lib*.a")
                    for lib in libs:
                        vslib = lib[3:-2] + ".lib"
                        self.output.info('renaming %s into %s' % (lib, vslib))
                        shutil.move(lib, vslib)
            else:
                autotools = self._configure_autotools()
                autotools.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
