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

"""
This module wraps ArgumentParser ideomatically and allows to work with the tool
menu in CRUTCH related terms and not just parsers and subparsers
"""

import argparse


class Menu(object):

  def __init__(self, *args, **kwargs):
    self.parser = argparse.ArgumentParser(*args, **kwargs)
    self.subparsers = self.parser.add_subparsers(title='Features', dest='run_feature')

  def add_feature(self, name, desc, group_prefix='feature', prefix_with_name=True):
    return MenuFeature(
        group_prefix + ('_' + name if prefix_with_name else ''),
        self.subparsers.add_parser(name, help=desc))

  def print_help(self):
    self.parser.print_help()

  def parse(self, line):
    return self.parser.parse_args(line)


class MenuActions(object):

  def __init__(self, name, subparser):
    self.subparser = subparser
    self.name = name

  def add_default(self, desc=''):
    return self.add_action('default', desc)

  def add_action(self, name, desc=''):
    return MenuAction(self.name + '_' + name, self.subparser.add_parser(name, help=desc))


class MenuAction(object):

  def __init__(self, name, parser):
    self.parser = parser
    self.name = name

  def add_argument(self, *args, **kwargs):
    if 'dest' not in kwargs:
      raise Exception("You must always provide `dest` parameter")
    kwargs['dest'] = self.name + '_' + kwargs['dest']
    self.parser.add_argument(*args, **kwargs)


class MenuFeature(MenuAction):

  def __init__(self, name, parser):
    super(MenuFeature, self).__init__(name, parser)
    self.parser.add_argument(
        '-d', '--directory', dest='project_directory', default='.',
        metavar='DIRECTORY', help='Target directory(default=curwd())')

  def add_actions(self):
    return MenuActions(self.name, self.parser.add_subparsers(title='Action', dest='action'))


def create_crutch_menu():
  """
  Create the main start menu for CRUTCH, this menu creates `new` feature menu
  explicitly since it must be available BEFORE runner is intialized and any
  features are available. Further feature invocation will be performed basing
  on config data
  """
  menu = Menu(prog='CRUTCH', description='Get a project running fast')

  new = menu.add_feature('new', 'Create a project', group_prefix='project', prefix_with_name=False)

  new.add_argument(
      dest='type', metavar='TYPE',
      choices=['cpp', 'python'], help='Project type')

  new.add_argument(
      '-n', '--name', metavar='NAME', dest='name',
      help='Project name(default=basename(FOLDER))')

  new.add_argument(
      '-f', '--features', metavar='FEATURE', nargs='*', default='default',
      dest='features', help='Select project features')

  return menu

def get_default_crutch_opts():
  return {'action': 'default', 'project_directory': '.'}
