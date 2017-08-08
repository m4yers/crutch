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

""" Main parser setup"""

import argparse

def get_parser():

  parser = argparse.ArgumentParser(
      prog='Crutch',
      description='Get a project running fast')

  subparsers = parser.add_subparsers(title='Actions', dest='action')

#------------------------------------------------------------------------------#
# Create
#------------------------------------------------------------------------------#
  parser_create = subparsers.add_parser('new', help='Create new project')

  parser_create.add_argument(
      'project_type', metavar='TYPE',
      choices=['cpp', 'python'], help='Project type')

  parser_create.add_argument(
      'project_folder', metavar='FOLDER', default='.',
      nargs='?', help='Project folder(default=curcwd())')

  parser_create.add_argument(
      '-n', '--name', metavar='NAME', dest='project_name',
      help='Project name(default=basename(FOLDER))')

  parser_create.add_argument(
      '-f', '--features', metavar='FEATURES', nargs='*',
      dest='project_features', help='Select project features')

#------------------------------------------------------------------------------#
# Build
#------------------------------------------------------------------------------#
  parser_build = subparsers.add_parser('build', help='Build the project')

  parser_build.add_argument(
      'project_folder', metavar='FOLDER', default='.',
      nargs='?', help='Project folder(default=curcwd())')

  parser_build.add_argument(
      '-c', '--config', metavar='CONFIG',
      dest='build_config', default='debug', choices=['debug', 'release'],
      help='Select project config')

  return parser
