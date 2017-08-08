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

import crutch.core.menu as Menu

from crutch.core.runner import RunnerEnvironment

class Driver(object):

  def __init__(self, runners, argv=None):
    self.runners = runners
    if argv is None:
      argv = sys.argv
    self.argv = argv

  def create_runner(self, opts):
    opts = vars(opts)

    templates = resource_filename(Requirement.parse('crutch'), 'templates')
    jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(templates))

    project_folder = os.path.abspath(opts.get('project_folder'))

    renv = RunnerEnvironment(jenv, opts, os.path.join(project_folder, '.crutch'))

    defaults = renv.get_default_properties()
    defaults['sys_user'] = os.getlogin()
    defaults['sys_python'] = sys.executable
    defaults['project_config'] = project_folder + '/.crutch'
    defaults['project_folder'] = project_folder

    stage = renv.get_stage_properties()

    if opts.get('action') == 'new':
      stage['project_name'] = opts.get('project_name') or os.path.basename(project_folder)
      stage['user_name'] = defaults['sys_user']
    else:
      renv.config_load()

    renv.mirror_props_to_repl(stage.keys())
    renv.mirror_props_to_config(stage.keys() + ['project_type'])

    # print renv.props.get_print_info()
    # print renv.repl.get_print_info()
    # renv.config_flush()
    # sys.exit(0)

    return renv, self.runners.get(renv.get_prop('project_type'))(renv)

  def run(self):
    opts = Menu.get_parser().parse_args(self.argv[1:])
    renv, runner = self.create_runner(opts)

    # print renv.props.get_print_info()
    # print renv.repl.get_print_info()
    # renv.config_flush()
    # sys.exit(0)

    runner.run()

    # print renv.props.get_print_info()
    # print renv.repl.get_print_info()

    renv.config_flush()
