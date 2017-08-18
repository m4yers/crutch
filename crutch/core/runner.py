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
import sys
import os

import networkx as nx

from crutch.core.properties import Properties
from crutch.core.replacements import Replacements


class RuntimeEnvironment(object):
  """
  Object of this class holds all necessary utility to get runner run
  """

  def __init__(self, menu, runners):
    self.menu = menu
    self.runners = runners
    self.props = Properties()
    self.repl = Replacements()
    self.prop_to_repl_mirror = self.repl.add_provider('prop_to_repl_mirror', dict())
    self.feature_ctrl = None

  def set_feature_ctrl(self, ctrl):
    self.feature_ctrl = ctrl

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

  def get_crutch_directory(self):
    return self.get_prop('crutch_directory')

  def get_project_directory(self):
    return self.get_prop('project_directory')

  def get_project_name(self):
    return self.get_prop('project_name')

  def get_project_type(self):
    return self.get_prop('project_type')

  def get_prop(self, name, default=None):
    return self.props.get(name, default)

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

  def __init__(self, name, init, features, defaults, requires, singular):
    self.name = name
    self.init = init
    self.features = features or list()
    self.defaults = defaults or list()
    self.requires = requires or list()
    self.singular = singular


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
      defaults=None, requires=None, singular=True):
    self.categories[cat_name] = \
        Category(cat_name, cat_class, features, defaults, requires, singular)
    for feat_name in features:
      self.feature_to_category[feat_name] = cat_name

  def register_feature_class(self, feat_name, feature_class):
    self.features[feat_name] = Feature(feat_name, feature_class, None)

  def is_category(self, name):
    return name in self.categories

  def is_feature(self, name):
    return name in self.features

  def get_category_and_features(self, req):
    req_cat_name = None
    req_cat_feat = list()

    if self.is_category(req):
      req_cat_name = req
      req_cat_feat.extend(self.categories[req].defaults)
    elif self.is_feature(req):
      req_cat_name = self.feature_to_category[req]
      req_cat_feat.append(req)
    else:
      raise Exception('Requirement {} is not provided'.format(req))

    return req_cat_name, req_cat_feat

  def normalize_project_features(self):
    project_features = self.renv.get_prop('project_features')

    result = dict()

    if project_features == 'default':
      for cat_name, cat in self.categories.items():
        if cat.defaults:
          result[cat_name] = cat.defaults

    elif project_features:

      for name in project_features:

        if self.is_category(name):
          if name in result:
            raise Exception('You must not pass features while using general category')
          result[name] = self.categories[name].defaults

        elif self.is_feature(name):
          cat_name = self.feature_to_category[name]
          cat = self.categories[cat_name]
          if cat_name in result and cat.singular:
            raise Exception('You cannot pass multiple features for a singular category')
          features = result.get(cat_name, list())
          features.append(name)
          result[cat_name] = features

    return result

  def build_dependency_graph(self, cat_to_feats):
    cat_queue = cat_to_feats.keys()
    graph = nx.DiGraph()
    graph.add_nodes_from(cat_queue)
    marked = set()
    while cat_queue:
      cat_name = cat_queue.pop()

      # This is a circular dependency. Cycles will be reported later
      if cat_name in marked:
        continue

      marked.add(cat_name)
      cat = self.categories[cat_name]

      # Add dependencies for the category itself
      for req in cat.requires:
        if self.is_category(req):
          req_cat_name = req
          # If required category is not already in the graph, add it and queue
          # it for the next cycle to process
          if req_cat_name not in cat_to_feats:
            graph.add_edge(req_cat_name, cat_name)
            cat = self.categories[req_cat_name]
            cat_to_feats[req_cat_name] = cat.defaults
            cat_queue.append(req_cat_name)
        elif self.is_feature(req):
          req_cat_name = self.feature_to_category[req]
          cat = self.categories[req_cat_name]

          # If required category is not already in the graph, add it with just
          # this feature  and queue it for the next cycle to process
          if req_cat_name not in cat_to_feats:
            cat = self.categories[req_cat_name]
            cat_to_feats[req_cat_name] = [req]
            cat_queue.append(req_cat_name)

          # Otherwise append the feature to the list
          elif not cat.singular:
            cat_to_feats[req_cat_name].append(req)

          graph.add_edge(req_cat_name, cat_name)

    return graph, cat_to_feats

  def get_init_order(self):
    """
    Build category and feature instantiation order
    """
    cat_to_feats = self.normalize_project_features()
    graph, cat_to_feats = self.build_dependency_graph(cat_to_feats)

    # If not DAG we cannot build graph's topology
    if not nx.is_directed_acyclic_graph(graph):
      print 'Features you have provided form a circular dependency:'
      print list(nx.find_cycle(graph, orientation='ignore'))
      sys.exit(1)

    cat_order = list(nx.topological_sort(graph))

    # Collect all features in category instantiation order
    feat_order = list()
    for cat_name in cat_order:
      feat_order.extend(cat_to_feats[cat_name])

    return cat_order, feat_order

  def activate(self):
    renv = self.renv
    cat_order, feat_order = self.get_init_order()

    for cat_name in cat_order:
      cat = self.categories[cat_name]
      cat_instance = cat.init(
          renv,
          {n: self.features[n].init for n in cat.features})
      cat_active_features = [f for f in feat_order if f in cat.features]
      cat_instance.activate_features(cat_active_features)
      self.active_categories[cat_name] = cat_instance

      renv.set_prop('project_feature_category_' + cat_name, True, mirror_to_repl=True)
      for feat_name in cat_active_features:
        renv.set_prop('project_feature_' + feat_name, True, mirror_to_repl=True)

    renv.set_prop('project_features', feat_order, mirror_to_config=True)

  def invoke(self, feature):
    category = self.active_categories.get(feature, None)
    if category:
      category.handle()
      return

    cat_name = self.feature_to_category[feature]
    self.active_categories[cat_name].handle_feature(feature)

  def get_active_category(self, name):
    assert name in self.active_categories
    return self.active_categories[name]

  def get_active_feature(self, name):
    cat_name = self.feature_to_category[name]
    assert cat_name in self.active_categories
    cat = self.active_categories[cat_name]
    return cat.get_active_feature(name)

  def get_singular_active_feature(self, cat_name):
    assert cat_name in self.active_categories
    cat = self.active_categories[cat_name]
    return cat.get_active_features()[0]


class Runner(object):

  def __init__(self, renv):
    self.renv = renv
    self.feature_ctrl = FeatureCtrl(renv)
    self.default_run_feature = None

    self.renv.set_feature_ctrl(self.feature_ctrl)

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
