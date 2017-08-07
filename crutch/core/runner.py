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

from crutch.core.features import Features

RE_VERSION = re.compile(r'\d+\.\d+\.\d+')
RE_DOT_HIDDEN = re.compile(r'.*/\..*$')
RE_PROJECT_NAME = re.compile(r'project|ProjectName')
RE_JINJA_EXT = re.compile(r'\.(j2|jinja|jinja2)$')
RE_JINJA_FILE = re.compile(r'.*\.(j2|jinja|jinja2)$')


class Runner(object):
  """Runner"""

  def __init__(self, opts, env, repl, cfg, features=Features):
    self.opts = opts
    self.env = env
    self.repl = repl
    self.cfg = cfg
    self.features = features()

    self.parse_config()
    self.init_project_features()

    self.dispatchers = {
        'new':   self.create,
        'build': self.build,
        'clean': self.clean,
        'info':  self.info
        }

  def init_project_features(self):
    project_features = self.opts.get('project_features') or \
      self.repl.get('project_features') or 'default'

    if project_features != 'default':
      self.features.parse(project_features)

    self.repl['project_features'] = ','.join(self.features.get_enabled_features())

    for category in self.features.get_enabled_categories():
      self.repl['project_has_feature_category_' + category] = True

    for feature in self.features.get_enabled_features():
      self.repl['project_has_feature_' + feature] = True

  def init_project_folder(self):
    project_type = self.repl['project_type']
    project_name = self.repl['project_name']
    project_folder = self.repl['project_folder']

    # Existing config file means a project already exists
    if os.path.exists(self.repl.get('file_config')):
      print 'The "{}" project already exists. Exit.'.format(project_name)
      sys.exit(1)

    feats = self.features.get_enabled_features()
    folders = ['main'] + ['features' + os.path.sep + f for f in feats]

    for folder in folders:
      re_tmpl_prefix = re.compile(r'^' + project_type + os.path.sep + folder)
      templates = filter(re_tmpl_prefix.match, self.env.list_templates())

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

        tmpl = self.env.get_template(tmpl_src)

        # If the file is not a template just copy it
        if not RE_JINJA_FILE.match(filename):
          shutil.copyfile(tmpl.filename, filename)
          continue

        # Drop .jinja extension
        filename = RE_JINJA_EXT.sub('', filename)

        with codecs.open(filename, 'w', 'utf-8') as out:
          out.write(tmpl.render())

  def parse_config(self):
    if not self.cfg.has_section('project'):
      return

    self.repl['project_features'] = self.cfg.get('project', 'features').split(',')

  def update_config(self):
    pass

  def create(self):
    self.init_project_folder()

  def build(self):
    print '[NOT IMPLEMENTED] Runner.build' + self

  def clean(self):
    print '[NOT IMPLEMENTED] Runner.clean' + self

  def info(self):
    print '[NOT IMPLEMENTED] Runner.info' + self

  def run(self):
    action = self.opts.get('action')
    self.dispatchers.get(action)()
