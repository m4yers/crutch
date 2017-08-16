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

import networkx as nx

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

  def __init__(self, name, init, features, defaults, requires):
    self.name = name
    self.init = init
    self.features = features or list()
    self.defaults = defaults or list()
    self.requires = requires or list()


class Feature(object):

  def __init__(self, name, init, requires):
    self.name = name
    self.init = init
    self.requires = requires or list()


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

  def register_feature_category_class(self, cat_name, cat_class, features,\
      defaults=None, requires=None):
    self.categories[cat_name] = Category(cat_name, cat_class, features, defaults, requires)
    for feat_name in features:
      self.feature_to_category[feat_name] = cat_name

  def register_feature_class(self, feat_name, feature_class, requires=None):
    self.features[feat_name] = Feature(feat_name, feature_class, requires)

  def add_category_dependency(self, graph, cat_name, req):
    req_cat_name = None
    if req in self.categories:
      req_cat_name = req
    elif req in self.features:
      req_cat_name = self.feature_to_category[req]
    else:
      raise Exception('Requirement {} is not provided'.format(req))
    graph.add_edge(req_cat_name, cat_name)


  def get_init_order(self):
    """
    Validate whether dependency graph is correct and can be used to instantiate
    all the categories and features
    """
    renv = self.renv
    project_features = renv.get_prop('project_features')

    # Find out the category instantiation order
    graph = nx.DiGraph()
    categories = list()
    if project_features == 'default':
      for cat_name, cat in self.categories.items():
        if cat.defaults:
          categories.append(cat_name)
    elif project_features:
      for feat_name in project_features:
        categories.append(self.feature_to_category[feat_name])

    graph.add_nodes_from(categories)
    for cat_name in categories:
      cat = self.categories[cat_name]

      # Add dependencies of the category itself
      for req in cat.requires:
        self.add_category_dependency(graph, cat_name, req)

      # Add dependencies of the category's features
      for feat_def_name in cat.defaults:
        for req in self.features[feat_def_name].requires:
          self.add_category_dependency(graph, cat_name, req)

    cat_order = list(reversed(list(nx.dfs_postorder_nodes(graph))))

    # Collect all features in category instantiation order
    feat_order = list()
    if project_features == 'default':
      for cat_name in cat_order:
        cat = self.categories[cat_name]
        if cat.defaults:
          feat_order.extend(cat.defaults)
    elif project_features:
      for cat_name in cat_order:
        cat = self.categories[cat_name]
        for feat_name in cat.features:
          if feat_name in project_features:
            feat_order.append(feat_name)

    return cat_order, feat_order

  def activate(self):
    renv = self.renv
    cat_order, feat_order = self.get_init_order()

    for cat_name in cat_order:
      cat = self.categories[cat_name]
      cat_instance = cat.init(
          renv,
          {n: self.features[n].init for n in cat.features})
      cat_instance.activate_features([f for f in feat_order if f in cat.features])
      self.active_categories[cat_name] = cat_instance

    renv.set_prop('project_features', feat_order, mirror_to_config=True)

  def invoke(self, feature):
    category = self.active_categories.get(feature, None)
    if category:
      category.handle_features()
      return

    cat_name = self.feature_to_category[feature]
    self.active_categories[cat_name].handle_feature(feature)


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
