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

import ConfigParser
import sys
import os

from pkg_resources import Requirement, resource_filename

import jinja2

import crutch.core.menu as Menu

class Driver(object):

  def __init__(self, runners, argv=None):
    self.runners = runners
    if argv is None:
      argv = sys.argv
    self.argv = argv

  def create_runner(self, opts):
    opts = vars(opts)

    templates = resource_filename(Requirement.parse('crutch'), 'templates')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates))

    project_folder = os.path.abspath(opts.get('project_folder'))

    repl = env.globals
    repl.update(opts)

    repl['python'] = sys.executable
    repl['project_folder'] = project_folder
    repl['file_config'] = project_folder + '/.crutch'

    cfg = ConfigParser.RawConfigParser()

    if opts.get('action') == 'new':
      repl['user'] = os.getlogin()
      repl['project_type'] = opts.get('project_type')
      repl['project_name'] = opts.get('project_name') or os.path.basename(project_folder)
    else:
      cfg.read(repl['file_config'])
      repl['user'] = cfg.get('project', 'type')
      repl['project_type'] = cfg.get('project', 'type')
      repl['project_name'] = cfg.get('project', 'name')

    return self.runners.get(repl['project_type'])(opts, env, repl, cfg)

  def run(self):
    opts = Menu.get_parser().parse_args(self.argv[1:])
    runner = self.create_runner(opts)
    runner.run()
