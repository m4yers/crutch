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

import sys
import os
import io

from crutch.core.menu import create_crutch_menu
from crutch.core.runtime import RuntimeEnvironment

import crutch.core.lifecycle as Lifecycle

class Driver(object):

  def __init__(self, runners, argv=None):
    self.runners = runners
    if argv is None:
      argv = sys.argv
    self.argv = argv

  def get_version(self):
    version = os.path.join(os.path.dirname(__file__), '..', '..', 'VERSION')
    with io.open(version) as out:
      return out.read().strip()

  def check_version(self, renv):
    config_version = renv.props.config.get('crutch_version')
    config_version_parts = config_version.split('.')
    this_version = renv.props.defaults.get('crutch_version')
    this_version_parts = this_version.split('.')

    # Major version mismatch is a no go
    if config_version_parts[0] != this_version_parts[0]:
      print 'Major versions are not compatible: project({}) vs crutch({})'\
          .format(config_version, this_version)
      sys.exit(1)

    # Minor version of the project cannot be bigger than CRUTCH's
    if config_version_parts[1] > this_version_parts[1]:
      print 'Minor versions are not compatible: project({}) vs crutch({})'\
          .format(config_version, this_version)
      sys.exit(1)

  def create_runtime_environment(self):
    renv = RuntimeEnvironment(self.runners)
    menu = create_crutch_menu(renv)
    renv.menu = menu

    defaults = renv.get_default_properties()
    defaults['crutch_python'] = sys.executable
    defaults['crutch_version'] = self.get_version()

    renv.mirror_props_to_config(defaults.keys())

    defaults['sys_login'] = os.getlogin()

    return renv

  def handle_new(self, renv):
    opts = renv.menu.parse(renv.get_prop('crutch_argv'))
    renv.update_cli_properties(opts)

    project_directory = renv.get_project_directory()
    crutch_directory = os.path.join(project_directory, '.crutch')
    crutch_config = os.path.join(project_directory, '.crutch.json')
    renv.set_prop('project_directory', project_directory)
    renv.set_prop('crutch_directory', crutch_directory)
    renv.set_prop('crutch_config', crutch_config)

    if os.path.exists(crutch_directory):
      print "You cannot invoke `new` on already existing CRUTCH directory"
      sys.exit(1)

    os.makedirs(crutch_directory)

    renv.update_config_filename(crutch_config)

    runner = self.runners.get('new')(renv)
    runner.activate_features()

    return runner

  def handle_no_args(self, renv):
    # Before we parse anything we need to load current config
    project_directory = os.path.abspath('.')
    crutch_directory = os.path.join(project_directory, '.crutch')
    crutch_config = os.path.join(project_directory, '.crutch.json')
    renv.set_prop('project_directory', project_directory)
    renv.set_prop('crutch_directory', crutch_directory)
    renv.set_prop('crutch_config', crutch_config)

    if not os.path.exists(crutch_config):
      print "You cannot invoke default CRUTCH action on non-initialized directory"
      sys.exit(1)

    # Current config gives us project type, and this type gives us default
    # feature and action to run
    renv.update_config_filename(crutch_config)
    renv.config_load()

    self.check_version(renv)

    runner = self.runners.get(renv.get_prop('project_type'))(renv)
    runner.activate_features()

    opts = renv.menu.parse([runner.default_run_feature])
    renv.update_cli_properties(opts)

    return runner

  def handle_normal(self, renv):
    # Before we parse anything we need to load current config
    project_directory = os.path.abspath('.')
    crutch_directory = os.path.join(project_directory, '.crutch')
    crutch_config = os.path.join(project_directory, '.crutch.json')
    renv.set_prop('project_directory', project_directory)
    renv.set_prop('crutch_directory', crutch_directory)
    renv.set_prop('crutch_config', crutch_config)

    if not os.path.exists(crutch_config):
      print "You cannot invoke default CRUTCH action on non-initialized directory"
      sys.exit(1)

    # Current config gives us project type, and this type gives us default
    # feature and action to run
    renv.update_config_filename(crutch_config)
    renv.config_load()

    self.check_version(renv)

    runner = self.runners.get(renv.get_prop('project_type'))(renv)
    runner.activate_features()

    opts = renv.menu.parse(renv.get_prop('crutch_argv'))
    renv.update_cli_properties(opts)

    return runner


  def run(self):
    # Before we start parsing the cli options we need a fully initialized
    # runtime environment
    renv = self.create_runtime_environment()
    # renv.lifecycle.enable_tracing()
    renv.lifecycle.mark(Lifecycle.CRUTCH_START)

    argv = self.argv[1:]
    renv.set_prop('crutch_argv', argv)

    runner = None
    if not argv:
      runner = self.handle_no_args(renv)
    elif argv[0] == 'new':
      runner = self.handle_new(renv)
    else:
      runner = self.handle_normal(renv)

    runner.run()

    runner.deactivate_features()

    # print renv.props.get_print_info()
    # print renv.repl.get_print_info()

    renv.config_flush()

    renv.lifecycle.mark(Lifecycle.CRUTCH_STOP)
    sys.exit(0)
