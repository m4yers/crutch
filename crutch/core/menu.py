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
import os

import crutch.core.lifecycle as Lifecycle

from crutch.core.exceptions import StopException


class MenuArgument(object):

  TYPE_POSITIONAL = 0
  TYPE_OPTIONAL = 1

  def __init__(self, short_name=None, long_name=None, **kwargs):
    self.kwargs = kwargs
    self.choices = kwargs.get('choices', None)
    self.default = kwargs.get('default', None)
    self.metavar = kwargs.get('metavar', None)
    self.nargs = kwargs.get('nargs', 1)
    self.help = kwargs.get('help', None)

    if short_name or long_name:
      self.type = MenuArgument.TYPE_OPTIONAL
      self.short_name = short_name
      self.long_name = long_name
    else:
      self.type = MenuArgument.TYPE_POSITIONAL
      self.short_name = self.long_name = None

  def __repr__(self):
    return '[Argument {} {}]'.format(
        'optional' if self.is_optional() else 'positional',
        self.long_name)

  def add_argument(self, parser):
    if self.is_positional():
      parser.add_argument(**self.kwargs)
    else:
      parser.add_argument(self.short_name, self.long_name, **self.kwargs)

  def is_positional(self):
    return self.type == MenuArgument.TYPE_POSITIONAL

  def is_optional(self):
    return self.type == MenuArgument.TYPE_OPTIONAL


class Menu(object):

  def __init__(self, renv, *args, **kwargs):
    self.renv = renv
    self.parser = argparse.ArgumentParser(*args, **kwargs)
    self.subparsers = self.parser.add_subparsers(title='Features', dest='run_feature')
    self.arguments = list()
    self.features = dict()

  def add_argument(self, short_name=None, long_name=None, **kwargs):
    argument = MenuArgument(short_name, long_name, **kwargs)
    argument.add_argument(self.parser)
    self.arguments.append(argument)

  def add_feature(self, name, desc):
    feature = MenuFeature(name, self.subparsers.add_parser(name, help=desc))
    self.features[name] = feature
    return feature

  def print_help(self):
    self.parser.print_help()

  def parse(self, argv):
    # Prepend with 'default' if necessary
    self.renv.lifecycle.mark(Lifecycle.CMD_PARSE, Lifecycle.ORDER_BEFORE, argv)
    feature = argv[0]
    if feature not in self.features:
      raise StopException(StopException.EFTR, "Feature '{}' is not enabled".format(feature))

    argv = argv[1:]
    if argv:
      actions = self.features[feature].actions
      action = argv[0]
      if not actions or action in actions.get_names():
        argv = [feature] + argv
      else:
        argv = [feature, 'default'] + argv
    else:
      argv = [feature, 'default']

    self.renv.lifecycle.mark(Lifecycle.CMD_PARSE, Lifecycle.ORDER_AFTER)

    try:
      opts = vars(self.parser.parse_args(argv))
    except SystemExit:
      raise StopException(StopException.EPAR)

    # Normalize project_directory
    opts['project_directory'] = os.path.abspath(opts['project_directory'])
    self.renv.update_cli_properties(opts)


class MenuActions(object):

  def __init__(self, name, subparser):
    self.subparser = subparser
    self.name = name
    self.actions = dict()

  def add_action(self, name, desc=''):
    action = MenuAction(name, self.subparser.add_parser(name, help=desc))
    self.actions[name] = action
    return action

  def get_names(self):
    return self.actions.keys()


class MenuAction(object):

  def __init__(self, name, parser):
    self.parser = parser
    self.name = name
    self.arguments = list()

  def add_argument(self, short_name=None, long_name=None, **kwargs):
    argument = MenuArgument(short_name, long_name, **kwargs)
    argument.add_argument(self.parser)
    self.arguments.append(argument)


class MenuFeature(MenuAction):

  def __init__(self, name, parser):
    super(MenuFeature, self).__init__(name, parser)
    self.parser.add_argument(
        '-d', '--directory', dest='project_directory', default='.',
        metavar='DIRECTORY', help='Target directory(default=curwd())')
    self.actions = None

  def add_actions(self):
    self.actions = MenuActions(
        self.name,
        self.parser.add_subparsers(title='Action', dest='action'))
    return self.actions


def create_crutch_menu(renv):
  """
  Create the main start menu for CRUTCH, this menu creates `new` feature menu
  explicitly since it must be available BEFORE runner is intialized and any
  features are available. Further feature invocation will be performed basing
  on config data
  """
  menu = Menu(renv, prog='CRUTCH', description='Get a project running fast')

  menu.add_argument('-p', '--prompt')

  return menu

def get_default_crutch_opts():
  return {'action': 'default', 'project_directory': '.'}
