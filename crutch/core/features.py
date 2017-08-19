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

import sys
import os

import networkx as nx

import crutch.core.lifecycle as Lifecycle

from crutch.core.replacements import GenerativeReplacementsProvider


class FeatureMenu(object):
  """
  FeatureMenu defines methods for assembling feature and feature category menus
  to be exposed to CRUTCH users
  """

  def __init__(self, renv, name, desc):
    self.name = name
    self.menu = renv.menu.add_feature(name, desc)
    self.actions = self.menu.add_actions()
    self.handlers = dict()

  def add_action(self, name, desc, handler):
    self.handlers[name] = handler
    return self.actions.add_action(name, desc)

  def add_default_action(self, desc, handler):
    return self.add_action('default', desc, handler)


class FeatureProto(object):
  """
  FeatureProto defines base behaviour of CRUTCH features and feature categories.
  This class defines method for menu registering, tear up/down and handling for
  handling basic feature requests
  """

  def __init__(self, renv):
    self.renv = renv
    self.menu = self.register_menu()

  def register_menu(self):
    """
    Here you create and return feature's menu actions if any
    """
    pass

  def activate(self):
    """
    Activation actions done by a feature or category. This is called whe
    CRUTCH is about to execute runner
    """
    pass

  def deactivate(self):
    """
    Deactivation actions done by a feature or category. This is called when
    CRUTCH is about to exit
    """
    pass


  def set_up(self):
    """
    Set up is called when a new feature is added during `new` invocation or
    afterwards using `feature` feature
    """
    pass

  def tear_down(self):
    """
    Tear down is called when a feature is removed by `feature` feature
    """
    pass

  def handle(self):
    pass


class Feature(FeatureProto):
  """
  Feature is something that defines and performs very narrow set of actions that
  cannot be split further
  """

  def __init__(self, renv):
    super(Feature, self).__init__(renv)
    self.register_properties()
    self.register_files()

  def register_files(self):
    """
    Here you add your feature files and folders, so they can be removed if
    a programmer decides to remove the feature. Also you may register any temp
    files or directories so `clean` feature may remove them
    """
    pass

  def register_properties(self):
    """
    Here you define/save all you properties to be mirrored to config or repl
    """
    project_directory = os.path.abspath(self.renv.get_prop('project_directory'))
    self.renv.set_prop('project_directory', project_directory)

  def handle(self):
    action = self.renv.get_prop('action')
    self.menu.handlers.get(action)()


class FeatureCategory(FeatureProto):
  """
  Feature category collects(usually) several features under a single name and
  can act as an interface for them exposing a common menu set. Every feature
  can be called separately as well.
  """

  def __init__(self, renv, features):
    super(FeatureCategory, self).__init__(renv)
    self.features = features
    self.active_features = dict()

  def activate_features(self, feature_names):
    map(self.activate_feature, feature_names)

  def activate_feature(self, feature_name):
    if feature_name in self.active_features:
      return
    self.renv.lifecycle.mark(Lifecycle.FEATURE_CREATE, Lifecycle.ORDER_BEFORE, feature_name)
    instance = self.features[feature_name](self.renv)
    self.active_features[feature_name] = instance
    instance.activate()
    self.renv.lifecycle.mark(Lifecycle.FEATURE_CREATE, Lifecycle.ORDER_AFTER, feature_name)

  def deactivate_feature(self, feature_name):
    self.renv.lifecycle.mark(Lifecycle.FEATURE_DESTROY, Lifecycle.ORDER_BEFORE, feature_name)
    feature = self.active_features.get(feature_name, None)
    if not feature:
      raise Exception("You cannot deactivate non-active feature")
    feature.deactivate()
    del self.active_features[feature_name]
    self.renv.lifecycle.mark(Lifecycle.FEATURE_DESTROY, Lifecycle.ORDER_BEFORE, feature_name)

  def get_active_feature_names(self):
    return self.active_features.keys()

  def get_active_features(self):
    return self.active_features.values()

  def get_active_feature(self, name):
    assert name in self.active_features
    return self.active_features[name]

  def set_up(self):
    for feature in self.active_features.values():
      feature.set_up()

  def tear_down(self):
    for feature in self.active_features.values():
      feature.tear_down()

  def handle(self):
    for feature in self.active_features.values():
      feature.handle()

  def handle_feature(self, feature_name):
    feature = self.active_features.get(feature_name, None)
    if not feature:
      raise Exception("You cannot handle non-active feature")
    feature.handle()


def create_simple_feature_category(menu):
  class SimpleFeatureCategoryWithMenu(FeatureCategory):
    def register_menu(self):
      return menu(self.renv)
  return SimpleFeatureCategoryWithMenu


class CategoryDesc(object):

  def __init__(self, name, init, features, defaults, requires, singular):
    self.name = name
    self.init = init
    self.features = features or list()
    self.defaults = defaults or list()
    self.requires = requires or list()
    self.singular = singular


class FeatureDesc(object):

  def __init__(self, name, init, requires):
    self.name = name
    self.init = init
    self.requires = requires or list()


class FeatureCtrlReplProvider(GenerativeReplacementsProvider):

  def __init__(self, renv):
    self.renv = renv
    GenerativeReplacementsProvider.__init__(self, dict())

  def generate(self):
    self.data = dict()
    for cat_name, cat_instance in self.renv.feature_ctrl.active_categories.items():
      self.data['project_feature_category_' + cat_name] = True
      for feat_name in cat_instance.get_active_feature_names():
        self.data['project_feature_' + feat_name] = True
    return self.data


class FeatureCtrl(object):

  def __init__(self, renv):
    self.renv = renv
    self.categories = dict()

    self.features = dict()
    self.feature_to_category = dict()

    self.active_categories = dict()

    renv.repl.add_provider('feature-ctrl-repl', FeatureCtrlReplProvider(renv))

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
        CategoryDesc(cat_name, cat_class, features, defaults, requires, singular)
    for feat_name in features:
      self.feature_to_category[feat_name] = cat_name

  def register_feature_class(self, feat_name, feature_class):
    self.features[feat_name] = FeatureDesc(feat_name, feature_class, None)

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
    requested_ftrs = sum([f for f in cat_to_feats.values()], [])
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

    return cat_order, feat_order, requested_ftrs

  def activate(self):
    self.renv.lifecycle.mark(Lifecycle.FEATURE_ACTIVATION, Lifecycle.ORDER_BEFORE)
    renv = self.renv
    cat_order, feat_order, requested_ftrs = self.get_init_order()

    for cat_name in cat_order:
      cat = self.categories[cat_name]
      cat_active_features = [f for f in feat_order if f in cat.features]
      cat_instance = self.active_categories.get(cat_name, None)

      if not cat_instance:
        self.renv.lifecycle.mark(Lifecycle.CATEGORY_CREATE, Lifecycle.ORDER_BEFORE, cat_name)
        cat_instance = cat.init(renv, {n: self.features[n].init for n in cat.features})
        cat_instance.activate()
        self.active_categories[cat_name] = cat_instance
        cat_instance.activate_features(cat_active_features)
        self.renv.lifecycle.mark(Lifecycle.CATEGORY_CREATE, Lifecycle.ORDER_AFTER, cat_name)
      else:
        cat_instance.activate_features(cat_active_features)

    self.renv.lifecycle.mark(Lifecycle.FEATURE_ACTIVATION, Lifecycle.ORDER_AFTER)

    return feat_order, requested_ftrs

  def deactivate(self):
    self.renv.lifecycle.mark(Lifecycle.FEATURE_DEACTIVATION, Lifecycle.ORDER_BEFORE)
    self.renv.lifecycle.mark(Lifecycle.FEATURE_DEACTIVATION, Lifecycle.ORDER_AFTER)

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

