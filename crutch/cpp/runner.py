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

""" This module defines C++ runner and supplements"""

import subprocess
import os

from crutch.core.runner import Runner

from crutch.cpp.features import CPPFeatures


class CPPRunner(Runner):
  """ C++ Runner """

  def __init__(self, opts, env, repl, cfg):
    super(CPPRunner, self).__init__(opts, env, repl, cfg, CPPFeatures)

  def parse_config(self):
    super(CPPRunner, self).parse_config()

    if not self.cfg.has_section('cpp'):
      return

    self.repl['cpp_cmake'] = self.cfg.get('cpp', 'cmake')
    self.repl['cpp_build'] = self.cfg.get('cpp', 'build')
    self.repl['cpp_install'] = self.cfg.get('cpp', 'install')

  def update_config(self):
    super(CPPRunner, self).parse_config()

  def configure(self):
    repl = self.repl

    build_config = self.repl.get('build_config')

    build_folder = repl['cpp_build']
    install_folder = repl['cpp_install']
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
        repl['cpp_cmake'],
        '-H' + repl['project_folder'],
        '-B' + build_folder,
        '-G"' + generator + '"',
        '-DCRUTCH_BUILD_TYPE=' + crutch_build_type,
        '-DCMAKE_BUILD_TYPE=' + cmake_build_type,
        '-DCMAKE_INSTALL_PREFIX=' + install_folder
        ]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

  def init_project_folder(self):
    super(CPPRunner, self).init_project_folder()

    project_folder = self.repl.get('project_folder')

    if self.features.is_doxygen():
      doc_folder = os.path.join(project_folder, 'doc')
      command = ['cd', doc_folder, '&&', 'doxygen', '-g', '-u', 'Doxyfile']
      subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

  def create(self):
    project_folder = self.repl['project_folder']

    self.repl['cpp_build'] = os.path.join(project_folder, '_build')
    self.repl['cpp_install'] = os.path.join(project_folder, '_install')
    self.repl['cpp_cmake'] = 'cmake'

    self.init_project_folder()

  def build(self):
    self.configure()

    build_config = self.repl.get('build_config')

    build_folder = self.repl['cpp_build']
    if self.features.is_make():
      build_folder += os.path.sep + build_config

    command = [self.repl['cpp_cmake'], \
        '--build', build_folder,       \
        '--config', build_config.capitalize()]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

