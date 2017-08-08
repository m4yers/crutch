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

from crutch.core.runner import Runner
from crutch.cpp.features import CPPFeatures


class CPPRunner(Runner):
  """ C++ Runner """

  def __init__(self, renv):
    super(CPPRunner, self).__init__(renv, CPPFeatures())

  def configure(self):
    build_config = self.renv.get_prop('build_config')
    project_folder = self.renv.get_prop('project_folder')


    build_folder = os.path.join(project_folder, self.renv.get_prop('cpp_build'))
    install_folder = os.path.join(project_folder, self.renv.get_prop('cpp_install'))
    if self.features.is_make():
      build_folder += os.path.sep + build_config
      install_folder += os.path.sep + build_config

    generators = {'xcode': 'Xcode', 'make': 'Unix Makefiles'}
    generator = generators.get(self.features.get_cmake_generator())

    cmake_build_type = build_config.capitalize()
    crutch_build_type = ''
    if self.features.is_xcode():
      crutch_build_type += cmake_build_type

    command = [
        self.renv.get_prop('cpp_cmake'),
        '-H' + self.renv.get_prop('project_folder'),
        '-B' + build_folder,
        '-G"' + generator + '"',
        '-DCRUTCH_BUILD_TYPE=' + crutch_build_type,
        '-DCMAKE_BUILD_TYPE=' + cmake_build_type,
        '-DCMAKE_INSTALL_PREFIX=' + install_folder
        ]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

  def init_project_folder(self):
    super(CPPRunner, self).init_project_folder()

    project_folder = self.renv.get_prop('project_folder')

    if self.features.is_doxygen():
      doc_folder = os.path.join(project_folder, 'doc')
      command = ['cd', doc_folder, '&&', 'doxygen', '-g', '-u', 'Doxyfile']
      subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

  def create(self):
    self.renv.set_prop('cpp_build', '_build', mirror_to_config=True)
    self.renv.set_prop('cpp_install', '_install', mirror_to_config=True)
    self.renv.set_prop('cpp_cmake', 'cmake', mirror_to_config=True)

    self.init_project_folder()

  def build(self):
    self.configure()

    build_config = self.renv.get_prop('build_config')
    build_folder = self.renv.get_prop('cpp_build')

    if self.features.is_make():
      build_folder += os.path.sep + build_config

    command = [self.renv.get_prop('cpp_cmake'), \
        '--build', build_folder,       \
        '--config', build_config.capitalize()]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

