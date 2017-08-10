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

import shutil
import os

from crutch.core.properties import Properties
from crutch.core.replacements import Replacements


class RuntimeEnvironment(object):
  """
  Object of this class holds all necessary utility to get runner run
  """

  def __init__(self, menu, jenv, runners):
    self.menu = menu
    self.jenv = jenv
    self.runners = runners
    self.props = Properties()
    self.repl = Replacements()
    self.prop_to_repl_mirror = self.repl.add_provider('prop_to_repl_mirror', dict())
    self.current_jinja_globals = list()

  def update_properties(self, props):
    self.props.update(props)

  def update_cli_properties(self, props):
    self.props.update_cli(props)

  def update_config_filename(self, config):
    self.props.update_config(config)

  def get_stage_properties(self):
    return self.props.stage

  def get_default_properties(self):
    return self.props.defaults

  def get_run_feature(self):
    return self.get_prop('run_feature')

  def get_project_features(self):
    return self.get_prop('project_features')

  def get_project_directory(self):
    return self.get_prop('project_directory')

  def get_prop(self, name):
    return self.props[name]

  def set_prop(self, name, value, mirror_to_config=False, mirror_to_repl=False):
    self.props[name] = value
    if mirror_to_config:
      self.mirror_props_to_config([name])
    if mirror_to_repl:
      self.mirror_props_to_repl([name])

  def set_prop_if_not_in(self, name, value, mirror_to_config=False, mirror_to_repl=False):
    if name not in self.props:
      self.set_prop(name, value, mirror_to_config, mirror_to_repl)

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


class TemporaryFilesManager(object):

  def __init__(self):
    self.files = list()
    self.directories = list()

  def add_file(self, path):
    self.files.append(path)

  def add_directory(self, path):
    self.directories.append(path)

  def clean(self):
    did_something = False
    for path in self.files:
      if os.path.exists(path):
        print "Deleting file '{}'".format(path)
        os.remove(path)
        did_something = True
    for path in self.directories:
      if os.path.exists(path):
        print "Deleting directory '{}'".format(path)
        shutil.rmtree(path)
        did_something = True
    if not did_something:
      print "Nothing to clean here..."
    else:
      print "Done"


class Category(object):

  def __init__(self, name, init, features, defaults):
    self.name = name
    self.init = init
    self.features = features
    self.defaults = defaults


class FeatureCtrl(object):

  def __init__(self, renv):
    self.renv = renv
    self.categories = dict()

    self.features = dict()
    self.feature_to_category = dict()

    self.active_categories = dict()

  def __repr__(self):
    result = 'FEATURE CTRL' + os.linesep + os.linesep
    for cat_name, cat in self.categories.items():
      result += ' '
      if cat_name in self.active_categories:
        result += '!'
      result += cat_name + os.linesep + '['
      for feat_name in cat.features:
        result += feat_name + ' '
      result += ']' + os.linesep

    return result

  def register_feature_category_class(self, cat_name, cat_class, features, defaults=None):
    self.categories[cat_name] = Category(cat_name, cat_class, features, defaults)
    for feature in features:
      self.feature_to_category[feature] = cat_name

  def register_feature_class(self, feat_name, feature_class):
    self.features[feat_name] = feature_class

  def activate(self):
    renv = self.renv
    project_features = renv.get_prop('project_features')
    # If default configuration is requested all default features from every
    # categoyr will be instantiated
    if project_features == 'default':
      project_features = list()
      for cat_name, cat in self.categories.items():
        if not cat.defaults:
          continue

        cat_instance = cat.init(
            self.renv,
            {name: self.features[name] for name in cat.features})

        project_features += cat.defaults

        cat_instance.activate_features(cat.defaults)
        self.active_categories[cat.name] = cat_instance

      renv.set_prop('project_features', project_features, mirror_to_config=True)

    # Otherwise instanciate only selected features and categories
    elif project_features:
      for feat_name, cat_name in self.feature_to_category.items():
        if feat_name not in project_features:
          continue

        cat_instance = self.active_categories.get(cat_name, None)

        if not cat_instance:
          cat = self.categories[cat_name]
          cat_instance = cat.init(
              self.renv,
              {name: self.features[name] for name in cat.features})
          self.active_categories[cat_name] = cat_instance

        cat_instance.activate_feature(feat_name)
        self.active_categories[cat_name] = cat_instance

  def invoke(self, feature):
    category = self.active_categories.get(feature, None)
    if category:
      category.handle()
      return

    cat_name = self.feature_to_category[feature]
    self.active_categories[cat_name].handle()


class Runner(object):

  def __init__(self, renv):
    self.renv = renv
    self.feature_ctrl = FeatureCtrl(renv)
    self.default_run_feature = None

  def register_default_run_feature(self, name):
    self.default_run_feature = name

  def register_feature_category_class(self, *args, **kwargs):
    self.feature_ctrl.register_feature_category_class(*args, **kwargs)

  def register_feature_class(self, *args, **kwargs):
    self.feature_ctrl.register_feature_class(*args, **kwargs)

  def activate_features(self):
    self.feature_ctrl.activate()

  def invoke_feature(self, name):
    self.feature_ctrl.invoke(name)

  def run(self):
    renv = self.renv
    self.activate_features()
    self.invoke_feature(renv.get_run_feature() or self.default_run_feature)
