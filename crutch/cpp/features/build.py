# -*- coding: utf-8 -*-

# Copyright © 2017 Artyom Goncharov
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import subprocess
import os

from crutch.core.features import Feature

class FeatureCppBuild(Feature):

  def __init__(self, renv, name, generator):
    self.name = name
    self.generator = generator
    self.build_directory_option = 'feature_{}_directory'.format(name)
    self.build_config_option = 'feature_{}_config'.format(name)
    super(FeatureCppBuild, self).__init__(renv)

  def get_build_directory_suffix(self):
    """
    This provides suffix name for the build directory. Usually this will be
    config type for build system that do pre-build configuration like make
    """
    return ''

  def register_actions(self, menu):
    build = menu.add_feature(self.name, 'Build C++ {} project'.format(self.generator))

    build.add_argument(
        '-c', '--config', dest='config', metavar='CONFIG',
        default='debug', choices=['debug', 'release'],
        help='Select project config')

  def register_properties(self):
    renv = self.renv
    renv.set_prop_if_not_in('cpp_cmake', 'cmake', mirror_to_config=True)
    renv.set_prop_if_not_in(self.build_directory_option, '_build', mirror_to_config=True)

  def get_build_directory(self):
    project_directory = self.renv.get_prop('project_directory')
    return os.path.abspath(
        os.path.join(
            project_directory,
            self.renv.get_prop(self.build_directory_option),
            self.get_build_directory_suffix()))

  def configure(self):
    build_config = self.renv.get_prop(self.build_directory_option)
    build_directory = self.get_build_directory()

    command = [
        self.renv.get_prop('cpp_cmake'),
        '-H' + self.renv.get_prop('project_directory'),
        '-B' + build_directory,
        '-G"' + self.generator + '"',
        '-DCMAKE_BUILD_TYPE=' + build_config.capitalize(),
        # '-DCMAKE_INSTALL_PREFIX=' + install_folder
        ]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

  def handle(self):
    build_config = self.renv.get_prop(self.build_config_option)
    build_directory = self.renv.get_prop(self.build_directory_option)

    # If not build folder we need to configure cmake first
    if not os.path.exists(build_directory):
      self.configure()

    command = [self.renv.get_prop('cpp_cmake'), \
        '--build', build_directory,       \
        '--config', build_config.capitalize()]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)


class FeatureCppBuildMake(FeatureCppBuild):

  def __init__(self, renv):
    super(FeatureCppBuildMake, self).__init__(renv, 'make', 'Unix Makefiles')

  def get_build_directory_suffix(self):
    return self.renv.get_prop(self.build_config_option)


class FeatureCppBuildXcode(FeatureCppBuild):

  def __init__(self, renv):
    super(FeatureCppBuildXcode, self).__init__(renv, 'xcode', 'Xcode')
