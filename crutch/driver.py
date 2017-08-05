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


from pkg_resources import Requirement, resource_filename
from jinja2 import Environment, FileSystemLoader, Template
import ConfigParser
import argparse
import string
import sys
import os

import runners


#------------------------------------------------------------------------------#
# MENU
#------------------------------------------------------------------------------#
parser = argparse.ArgumentParser(prog='Crutch',
    description='Get a project running fast')

subparsers = parser.add_subparsers(title='Actions', dest='action')

#------------------------------------------------------------------------------#
# Create
#------------------------------------------------------------------------------#
parser_create = subparsers.add_parser('new', help='Create new project')

parser_create.add_argument('project_type', metavar='TYPE',
    choices=['cpp', 'python'], help='Project type')

parser_create.add_argument('project_folder', metavar='FOLDER', default='.',
    nargs='?',help='Project folder(default=curcwd())')

parser_create.add_argument('-n', '--name', metavar='NAME',
    help='Project name(default=basename(FOLDER))')

parser_create.add_argument('-f', '--features', metavar='FEATURES',
    default='default', help='Select project features')

#------------------------------------------------------------------------------#
# Build
#------------------------------------------------------------------------------#
parser_build = subparsers.add_parser('build', help='Build the project')

parser_build.add_argument('project_folder', metavar='FOLDER', default='.',
    nargs='?',help='Project folder(default=curcwd())')


#------------------------------------------------------------------------------#
# DRIVER
#------------------------------------------------------------------------------#
class Driver(object):

  def __init__(self, argv=None):
    if argv is None:
      argv = sys.argv
    self.argv = argv

  def create_runner(self, opts):
    opts = vars(opts)

    templates = resource_filename(Requirement.parse('crutch'), 'templates')
    env = Environment(loader=FileSystemLoader(templates))

    project_folder = os.path.abspath(opts.get('project_folder'))

    repl = env.globals
    repl['python'] = sys.executable
    repl['project_folder'] = project_folder
    repl['file_config'] = project_folder + '/.crutch'

    cfg = ConfigParser.RawConfigParser()
    cfg.read(repl['file_config'])

    if opts.get('action') == 'new':
      repl['user'] = os.getlogin()
      repl['project_type'] = opts.get('project_type')
      repl['project_name'] = opts.get('project_name') or os.path.basename(project_folder)
    else:
      repl['user'] = cfg.get('project', 'type')
      repl['project_type'] = cfg.get('project', 'type')
      repl['project_name'] = cfg.get('project', 'name')

    return runners.get_runner(repl['project_type'])(opts, env, repl, cfg)

  def run(self):
    opts = parser.parse_args(self.argv[1:])
    runner = self.create_runner(opts)
    runner.run()
