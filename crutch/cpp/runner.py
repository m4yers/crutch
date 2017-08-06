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
import sys
import os

from core.runner import Runner


class CPPRunner(Runner):

  def __init__(self, opts, env, repl, cfg):
    super(CPPRunner, self).__init__(opts, env, repl, cfg)
    self.generators = {'xcode': 'Xcode', 'make': 'Unix Makefiles'}

  def get_generator(self):
    return self.generators.get(self.repl['cpp_generator'])

  def get_build_config(self):
    return self.repl.get('build_config').capitalize()

  def parse_config(self):
    if not self.cfg.has_section('cpp'):
      return

    self.repl['cpp_cmake']     = self.cfg.get('cpp', 'cmake')
    self.repl['cpp_generator'] = self.cfg.get('cpp', 'generator')
    self.repl['cpp_build']     = self.cfg.get('cpp', 'build')
    self.repl['cpp_install']   = self.cfg.get('cpp', 'install')

  def update_config(self):
    pass

  def configure(self):
    repl = self.repl

    command = [repl['cpp_cmake'],
      '-H' + repl['project_folder'],
      '-B' + repl['cpp_build'],
      '-G"' + self.get_generator() + '"',
      '-DCRUTCH_BUILD_TYPE=' + self.get_build_config(),
      '-DCMAKE_BUILD_TYPE=' + self.get_build_config(),
      '-DCMAKE_INSTALL_PREFIX=' + repl['cpp_install']
    ]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

  def create(self):
    repl = self.repl

    project_folder = repl['project_folder']

    repl['cpp_generator'] = 'xcode'
    repl['cpp_build']   = os.path.join(project_folder, '_build')
    repl['cpp_install'] = os.path.join(project_folder, '_install')
    repl['cpp_cmake']   = 'cmake'

    self.init_folder()

  def build(self):
    repl = self.repl

    self.configure()

    command = [repl['cpp_cmake'],
        '--build', repl['cpp_build'],
        '--config', self.get_build_config()]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

