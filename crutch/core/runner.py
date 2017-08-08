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

import codecs
import shutil
import sys
import re
import os

from crutch.core.properties import Properties
from crutch.core.replacements import Replacements

RE_VERSION = re.compile(r'\d+\.\d+\.\d+')
RE_DOT_HIDDEN = re.compile(r'.*/\..*$')
RE_PROJECT_NAME = re.compile(r'project|ProjectName')
RE_JINJA_EXT = re.compile(r'\.(j2|jinja|jinja2)$')
RE_JINJA_FILE = re.compile(r'.*\.(j2|jinja|jinja2)$')


class RunnerEnvironment(object):
  """
  Object of this class holds all necessary utility to get runner run
  """

  def __init__(self, jenv, cli, config):
    self.jenv = jenv
    self.props = Properties(dict(), config, cli)
    self.repl = Replacements()
    self.prop_to_repl_mirror = self.repl.add_provider('prop_to_repl_mirror', dict())
    self.current_jinja_globals = list()
    self.features = None

  def add_features(self, features):
    self.features = features
    self.repl.add_provider('features', features.get_repl_provider())

  def get_stage_properties(self):
    return self.props.stage

  def get_default_properties(self):
    return self.props.defaults

  def get_prop(self, name):
    return self.props[name]

  def set_prop(self, name, value, mirror_to_config=False, mirror_to_repl=False):
    self.props[name] = value
    if mirror_to_config:
      self.mirror_props_to_config([name])
    if mirror_to_repl:
      self.mirror_props_to_repl([name])

  def config_load(self):
    self.props.config_load()

  def config_flush(self):
    self.props.config_flush()

  def mirror_props_to_config(self, properties):
    for prop in properties:
      self.props.config_update(prop, self.props[prop])

  def mirror_props_to_repl(self, properties):
    """
    Copies every property in properties list from Properties container into
    Replacements containers. This method does not perform cleanup, and won't
    delete previously mirrored properties
    """

    for prop in properties:
      self.prop_to_repl_mirror[prop] = self.props[prop]

  def mirror_repl_to_jinja_globals(self):
    """
    Call this method before rendering any jenv template to populate the
    current_jinja_globals object with the most recent replacements
    """

    # First, delete already existing current_jinja_globals
    for glob in self.current_jinja_globals:
      del self.jenv.current_jinja_globals[glob]

    # Then, populate with fresh ones
    self.repl.fetch()
    self.jenv.globals.update(self.repl)


class Runner(object):
  """Runner"""

  def __init__(self, renv, features):
    self.renv = renv
    self.renv.add_features(features)
    self.features = features

    self.dispatchers = {
        'new':   self.create,
        'build': self.build,
        'clean': self.clean,
        'info':  self.info
        }

    self.init_project_features()

  def init_project_features(self):
    project_features = self.renv.get_prop('project_features') or 'default'

    if project_features != 'default':
      self.features.parse(project_features)

    features = self.features.get_enabled_features()
    self.renv.set_prop('project_features', features, mirror_to_config=True)

  def init_project_folder(self):
    project_type = self.renv.get_prop('project_type')
    project_name = self.renv.get_prop('project_name')
    project_folder = self.renv.get_prop('project_folder')

    # Existing config file means a project already exists
    if os.path.exists(self.renv.get_prop('project_config')):
      print 'The "{}" project already exists. Exit.'.format(project_name)
      sys.exit(1)

    features = self.features.get_enabled_features()
    folders = ['main'] + ['features' + os.path.sep + f for f in features]

    jenv = self.renv.jenv

    self.renv.mirror_repl_to_jinja_globals()

    for folder in folders:
      re_tmpl_prefix = re.compile(r'^' + project_type + os.path.sep + folder)
      templates = filter(re_tmpl_prefix.match, jenv.list_templates())

      for tmpl_src in templates:
        filename = re_tmpl_prefix.sub('', tmpl_src)
        filename = RE_PROJECT_NAME.sub(project_name, filename)
        filename = project_folder + filename

        # Do not override existing files
        if os.path.exists(filename):
          continue

        # Create the containing folder if does not exist already
        folder = os.path.dirname(filename)
        if not os.path.exists(folder):
          os.makedirs(folder)

        tmpl = jenv.get_template(tmpl_src)

        # If the file is not a template just copy it
        if not RE_JINJA_FILE.match(filename):
          shutil.copyfile(tmpl.filename, filename)
          continue

        # Drop .jenv extension
        filename = RE_JINJA_EXT.sub('', filename)

        with codecs.open(filename, 'w', 'utf-8') as out:
          out.write(tmpl.render())

  def create(self):
    self.init_project_folder()

  def build(self):
    print '[NOT IMPLEMENTED] Runner.build' + self

  def clean(self):
    print '[NOT IMPLEMENTED] Runner.clean' + self

  def info(self):
    print '[NOT IMPLEMENTED] Runner.info' + self

  def run(self):
    action = self.renv.get_prop('action')
    self.dispatchers.get(action)()
