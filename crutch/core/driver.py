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

from __future__ import unicode_literals
from __future__ import print_function

import sys
import os
import io

import crutch.core.lifecycle as Lifecycle

from crutch.core.exceptions import StopException
from crutch.core.runtime import RuntimeEnvironment
from crutch.core.menu import create_crutch_menu
from crutch.core.repl.prompt import Prompt

class Driver(object):

  def __init__(self, runners, argv=None):
    self.runners = runners
    self.argv = argv or sys.argv
    self.renv = None
    self.version = None

  def check_crutch_config(self):
    if not os.path.exists(self.renv.get_prop('crutch_config')):
      raise StopException(
          StopException.EPERM,
          'You cannot invoke default CRUTCH action on non-initialized directory')

  def get_version(self):
    if not self.version:
      version_file = os.path.join(os.path.dirname(__file__), '..', '..', 'VERSION')
      with io.open(version_file) as out:
        self.version = out.read().strip()
    return self.version

  def check_version(self):
    config_version = self.renv.props.config.get('crutch_version')
    config_version_parts = config_version.split('.')
    this_version = self.renv.props.defaults.get('crutch_version')
    this_version_parts = this_version.split('.')

    # Major version mismatch is a no go
    if config_version_parts[0] != this_version_parts[0]:
      raise StopException(
          StopException.EVER,
          'Major versions are not compatible: project({}) vs crutch({})'\
          .format(config_version, this_version))

    # Minor version of the project cannot be bigger than CRUTCH's
    if config_version_parts[1] > this_version_parts[1]:
      raise StopException(
          StopException.EVER,
          'Minor versions are not compatible: project({}) vs crutch({})'\
          .format(config_version, this_version))

  def create_runtime_environment(self):
    self.renv = RuntimeEnvironment(self.runners)
    self.renv.set_as_default() # Required by REPL lexer
    self.renv.menu = create_crutch_menu(self.renv)
    self.renv.prompt = Prompt(self.renv)
    return self.renv

  def set_default_props(self, project_directory=None):
    defaults = self.renv.get_default_properties()
    defaults['crutch_python'] = sys.executable
    defaults['crutch_version'] = self.get_version()

    self.renv.mirror_props_to_config(defaults.keys())

    defaults['sys_login'] = os.getlogin()

    project_directory = project_directory or self.renv.get_project_directory()
    self.renv.set_prop('project_directory', project_directory)
    self.renv.set_prop('crutch_directory', os.path.join(project_directory, '.crutch'))
    self.renv.set_prop('crutch_config', os.path.join(project_directory, '.crutch.json'))

  def handle_no_args(self):
    self.set_default_props(os.path.abspath('.'))
    self.check_crutch_config()
    self.renv.config_load()
    self.check_version()

    runner = self.renv.create_runner(self.renv.get_project_type())
    runner.activate_features()

    self.renv.menu.parse([runner.default_run_feature])

    return runner

  def handle_new(self):
    self.renv.set_prop('project_features', ['new'])

    runner = self.renv.create_runner('new')
    runner.activate_features()

    self.renv.del_prop('project_features')

    self.renv.menu.parse(self.renv.get_prop('crutch_argv'))
    self.set_default_props()

    if os.path.exists(self.renv.get_crutch_config()):
      raise StopException(
          StopException.EPERM,
          'You cannot invoke `new` on already existing CRUTCH directory')

    return runner

  def handle_normal(self):
    # FIND a way to get the directory from the argv before parsing
    # Maybe -d --directory should be top level e.g. crutch -d ~/blah build
    self.set_default_props(os.path.abspath('.'))
    self.check_crutch_config()
    self.renv.config_load()
    self.check_version()

    runner = self.renv.create_runner(self.renv.get_project_type())
    runner.activate_features()

    self.renv.menu.parse(self.renv.get_prop('crutch_argv'))

    return runner

  def handle_prompt(self):
    self.set_default_props(os.path.abspath('.'))

    crutch_config = self.renv.get_prop('crutch_config')

    runner = None

    # Since prompt syntax highlight depends on active features we need to read the config first
    # and activate all the features
    if os.path.exists(crutch_config):
      self.renv.config_load()
      self.check_version()
      self.set_default_props()
      runner = self.renv.create_runner(self.renv.get_project_type())
      runner.activate_features()

    # Otherwise we allow only new to run, and it will update runner upon success
    else:
      self.renv.create_runner('new').activate_features()

    print("CRUTCH {}".format(self.get_version()))
    print("Home: https://github.com/m4yers/crutch")

    self.renv.prompt.initialize()
    reinitialize_prompt = False

    while True:

      try:
        argv = self.renv.prompt.activate(reinitialize_prompt)
        reinitialize_prompt = False

        if not argv:
          continue

        elif argv[0] == 'new':
          if os.path.exists(crutch_config):
            raise StopException(
                StopException.EPERM,
                'You cannot invoke `new` on already existing CRUTCH directory')

          self.renv.menu.parse(argv)
          self.set_default_props()
          runner = self.renv.feature_ctrl.get_active_feature('new').create()
          reinitialize_prompt = True

        else:
          self.renv.menu.parse(argv)
          runner.run()

        self.renv.config_flush()
      except StopException as stop:
        if stop.terminate:
          raise
        if stop.message:
          print(stop.message)
        continue
      except KeyboardInterrupt:
        break
      except EOFError:
        break

    raise StopException()

  def run(self):
    code = StopException.EOK
    message = None

    try:
      renv = self.create_runtime_environment()
      renv.lifecycle.enable_tracing()
      renv.lifecycle.mark(Lifecycle.CRUTCH_START)

      argv = self.argv[1:]
      renv.set_prop('crutch_argv', argv)

      runner = None

      if not argv:
        runner = self.handle_no_args()
      elif argv[0] == '-p' or argv[0] == '--prompt':
        self.handle_prompt()
      elif argv[0] == 'new':
        runner = self.handle_new()
      else:
        runner = self.handle_normal()

      runner.run()

    except StopException as stop:
      code = stop.code
      message = stop.message

    try:
      renv.feature_ctrl.deactivate()
    except StopException as stop:
      code = stop.code
      message = stop.message

    if code == StopException.EOK:
      self.renv.config_flush()

    # print renv.props.get_print_info()
    # print renv.repl.get_print_info()

    renv.lifecycle.mark(Lifecycle.CRUTCH_STOP)

    if message:
      print(message)

    sys.exit(code)
