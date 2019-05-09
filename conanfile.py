#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


def sort_libs(correct_order, libs, lib_suffix='', reverse_result=False):
    # Add suffix for correct string matching
    correct_order[:] = [s.__add__(lib_suffix) for s in correct_order]

    result = []
    for expectedLib in correct_order:
        for lib in libs:
            if expectedLib == lib:
                result.append(lib)

    if reverse_result:
        # Linking happens in reversed order
        result.reverse()

    return result


class MagnumIntegrationConan(ConanFile):
    name = "magnum-plugins"
    version = "2019.01"
    description = (
        "Magnum Plugins - Plugins for the Magnum C++11/C++14 graphics engine")
    topics = ("conan", "corrade", "graphics", "rendering", "3d", "2d",
              "opengl")
    url = "https://github.com/rhololkeolke/conan-magnum-plugins"
    author = "helmesjo <helmesjo@gmail.com>"
    # Indicates license type of the packaged library; please use SPDX
    # Identifiers https://spdx.org/licenses/
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    # Some folders go out of the 260 chars path length scope (windows)
    short_paths = True

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_assimpimporter": [True, False],
        "with_ddsimporter": [True, False],
        "with_devilimageimporter": [True, False],
        "with_drflacaudioimporter": [True, False],
        "with_drwavaudioimporter": [True, False],
        "with_faad2audioimporter": [True, False],
        "with_freetypefont": [True, False],
        "with_harfbuzzfont": [True, False],
        "with_jpegimageconverter": [True, False],
        "with_miniexrimageconverter": [True, False],
        "with_openddl": [True, False],
        "with_opengeximporter": [True, False],
        "with_pngimageconverter": [True, False],
        "with_pngimporter": [True, False],
        "with_stanfordimporter": [True, False],
        "with_stbimageconverter": [True, False],
        "with_stbimageimporter": [True, False],
        "with_stbtruetypefont": [True, False],
        "with_stbvorbisaudioimporter": [True, False],
        "with_tinygltfimporter": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_assimpimporter": False,
        "with_ddsimporter": False,
        "with_devilimageimporter": False,
        "with_drflacaudioimporter": False,
        "with_drwavaudioimporter": False,
        "with_faad2audioimporter": False,
        "with_freetypefont": False,
        "with_harfbuzzfont": False,
        "with_jpegimageconverter": False,
        "with_miniexrimageconverter": False,
        "with_openddl": False,
        "with_opengeximporter": False,
        "with_pngimageconverter": False,
        "with_pngimporter": False,
        "with_stanfordimporter": False,
        "with_stbimageconverter": False,
        "with_stbimageimporter": False,
        "with_stbtruetypefont": False,
        "with_stbvorbisaudioimporter": False,
        "with_tinygltfimporter": False,
    }

    # Custom attributes for Bincrafters recipe conventions
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = ("magnum/2019.01@rhololkeolke/testing",
                "corrade/2019.01@rhololkeolke/testing")

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        # To fix issue with resource management, see here:
        # https://github.com/mosra/magnum/issues/304#issuecomment-451768389
        if self.options.shared:
            self.options['magnum'].add_option('shared', True)

    def requirements(self):
        if self.options.with_freetypefont and self.options.with_harfbuzzfont:
            raise RuntimeError(
                "Exclusive options selected! 'with_freetypefont' and "
                "'with_harfbuzzfont' cannot both be on.")
        if self.options.with_openddl and self.options.with_opengeximporter:
            raise RuntimeError("Exclusive options selected! 'with_openddl' "
                               "and 'with_opengeximporter' cannot both be on.")
        if self.options.with_assimpimporter:
            self.requires("Assimp/4.1.0@jacmoe/stable")
            self.options["magnum"].with_anyimageimporter = True

    def source(self):
        source_url = "https://github.com/mosra/magnum-plugins"
        tools.get("{0}/archive/v{1}.tar.gz".format(source_url, self.version))
        extracted_dir = self.name + "-" + self.version

        # Rename to "source_subfolder" is a convention to simplify later steps
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)

        def add_cmake_option(option, value):
            var_name = "{}".format(option).upper()
            value_str = "{}".format(value)
            var_value = "ON" if value_str == 'True' else "OFF" if value_str == 'False' else value_str
            cmake.definitions[var_name] = var_value

        for option, value in self.options.items():
            add_cmake_option(option, value)

        # Magnum uses suffix on the resulting 'lib'-folder when
        # running cmake.install() Set it explicitly to empty, else
        # Magnum might set it implicitly (eg. to "64")
        add_cmake_option("LIB_SUFFIX", "")

        add_cmake_option("BUILD_STATIC", not self.options.shared)
        add_cmake_option(
            "BUILD_STATIC_PIC", not self.options.shared
            and self.options.get_safe("fPIC"))

        cmake.configure(build_folder=self._build_subfolder)

        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(
            pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        allLibs = []
        if self.options.with_assimpimporter:
            allLibs.append("AssimpImporter")

        # Sort all built libs according to above, and reverse result
        # for correct link order
        suffix = '-d' if self.settings.build_type == "Debug" else ''
        builtLibs = tools.collect_libs(self)
        self.cpp_info.libs = sort_libs(
            correct_order=allLibs,
            libs=builtLibs,
            lib_suffix=suffix,
            reverse_result=True)
