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
import sys
import os

import crutch.core.lifecycle as Lifecycle


class Menu(object):

  def __init__(self, renv, *args, **kwargs):
    self.renv = renv
    self.parser = argparse.ArgumentParser(*args, **kwargs)
    self.subparsers = self.parser.add_subparsers(title='Features', dest='run_feature')
    self.features = dict()

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
      print "Feature '{}' is not enabled".format(feature)
      sys.exit(1)

    argv = argv[1:]
    if argv:
      actions = self.features[feature].get_actions()
      action = argv[0]
      if not actions or action in actions.get_names():
        argv = [feature] + argv
      else:
        argv = [feature, 'default'] + argv
    else:
      argv = [feature, 'default']

    self.renv.lifecycle.mark(Lifecycle.CMD_PARSE, Lifecycle.ORDER_AFTER)

    # Normalize project_directory
    opts = vars(self.parser.parse_args(argv))
    opts['project_directory'] = os.path.abspath(opts['project_directory'])

    return opts


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

  def add_argument(self, *args, **kwargs):
    self.parser.add_argument(*args, **kwargs)


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

  def get_actions(self):
    return self.actions


def create_crutch_menu(renv):
  """
  Create the main start menu for CRUTCH, this menu creates `new` feature menu
  explicitly since it must be available BEFORE runner is intialized and any
  features are available. Further feature invocation will be performed basing
  on config data
  """
  menu = Menu(renv, prog='CRUTCH', description='Get a project running fast')

  new = menu.add_feature('new', 'Create a project')

  new.add_argument(
      dest='project_type', metavar='TYPE',
      choices=['cpp', 'python'], help='Project type')

  new.add_argument(
      '-n', '--name', metavar='NAME', dest='project_name',
      help='Project name(default=basename(FOLDER))')

  new.add_argument(
      '-f', '--features', metavar='FEATURE', nargs='*', default='default',
      dest='project_features', help='Select project features')

  return menu

def get_default_crutch_opts():
  return {'action': 'default', 'project_directory': '.'}
