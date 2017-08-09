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

from pkg_resources import Requirement, resource_filename

import jinja2

from crutch.core.menu import create_crutch_menu, get_default_crutch_opts

from crutch.core.runner import RuntimeEnvironment

class Driver(object):

  def __init__(self, runners, argv=None):
    self.runners = runners
    if argv is None:
      argv = sys.argv
    self.argv = argv

  def create_runtime_environment(self, menu):
    templates = resource_filename(Requirement.parse('crutch'), 'templates')
    jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(templates))

    renv = RuntimeEnvironment(menu, jenv)

    defaults = renv.get_default_properties()
    defaults['os_login'] = os.getlogin()
    defaults['sys_python'] = sys.executable

    renv.mirror_props_to_repl(defaults.keys())
    renv.mirror_props_to_config(defaults.keys())

    return renv

  def handle_no_args(self):
    # opts = get_default_crutch_opts()
    return 0

  def handle_new(self, renv):
    opts = renv.menu.parse(renv.get_prop('sys_argv'))
    renv.update_cli_properties(vars(opts))

    project_directory = renv.get_project_directory()
    project_config = os.path.join(project_directory, '.crutch')

    if os.path.exists(project_config):
      print "You cannot invoke `new` on already existing CRUTCH directory"
      sys.exit(1)

    renv.update_config_properties(project_config)

    return self.runners.get('new')(renv)

  def handle_normal(self):
    return 0

  def run(self):
    menu = create_crutch_menu()

    # Before we start parsing the cli options we need a fully initialized
    # runtime environment
    renv = self.create_runtime_environment(menu)

    # print renv.props.get_print_info()
    # print renv.repl.get_print_info()
    # sys.exit(0)

    argv = self.argv[1:]
    renv.set_prop('sys_argv', argv)

    runner = None
    if not argv:
      runner = self.handle_no_args()
    elif argv[0] == 'new':
      runner = self.handle_new(renv)
    else:
      runner = self.handle_normal()

    # if renv.get_action() == 'default' and not os.path.exists(renv.get_prop('project_config')):
    #   print "You cannot invoke default action on non-crutch folder. Exiting..."
    #   sys.exit(1)

    print renv.props.get_print_info()
    print renv.repl.get_print_info()

    runner.run()

    print renv.props.get_print_info()
    print renv.repl.get_print_info()

    renv.config_flush()
