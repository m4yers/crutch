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

import os

import networkx as nx

import crutch.core.lifecycle as Lifecycle

from crutch.core.exceptions import StopException
from crutch.core.features.basics import FeatureCategory
from crutch.core.replacements import GenerativeReplacementsProvider

class CategoryDesc(object):

  def __init__(self, name, init, features, defaults, requires, singular, always):
    self.name = name
    self.init = init
    self.features = features or list()
    self.defaults = defaults or list()
    self.requires = requires or list()
    self.singular = singular
    self.always = always


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
    for cat_name, cat_inst in self.renv.feature_ctrl.active_categories.items():
      self.data['project_feature_category_' + cat_name] = True
      for feat_name in cat_inst.get_active_feature_names():
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

#-SUPPORT-----------------------------------------------------------------------

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

  def normalize_project_features(self, features):
    result = dict()

    if features == 'default':
      for cat_name, cat in self.categories.items():
        if cat.defaults:
          result[cat_name] = cat.defaults

    elif features:

      for name in features:

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

    # Always instantiated default CRUTCH category defaults
    crutch_category = self.categories['crutch']
    result['crutch'] = crutch_category.defaults

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

  def get_init_order(self, features):
    """
    Build category and feature instantiation order
    """
    cat_to_feats = self.normalize_project_features(features)
    # Ignore CRUTCH services, they are specially handler and do not require
    # explicit mentioning
    requested_ftrs = sum([cat_to_feats[c] for c in cat_to_feats if c != 'crutch'], [])
    graph, cat_to_feats = self.build_dependency_graph(cat_to_feats)

    # If not DAG we cannot build graph's topology
    if not nx.is_directed_acyclic_graph(graph):
      raise Exception(
          'Features you have provided form a circular dependency:\n' +
          list(nx.find_cycle(graph, orientation='ignore')))

    cat_order = list(nx.topological_sort(graph))

    # Collect all features in category instantiation order
    feat_order = list()
    for cat_name in cat_order:
      feat_order.extend(cat_to_feats[cat_name])

    return cat_order, feat_order, requested_ftrs

  def activate_features(self, features):
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_ACTIVATION)

    renv = self.renv
    cat_order, feat_order, requested_ftrs = self.get_init_order(features)

    for cat_name in cat_order:
      cat_desc = self.categories[cat_name]
      cat_active_features = [f for f in feat_order if f in cat_desc.features]
      cat_inst = self.active_categories.get(cat_name, None)

      if not cat_inst:
        self.renv.lifecycle.mark_before(Lifecycle.CATEGORY_CREATE, cat_name)
        cat_inst = cat_desc.init(
            renv,
            {n: self.features[n].init for n in cat_desc.features})
        cat_inst.activate()
        self.active_categories[cat_name] = cat_inst
        cat_inst.activate_features(cat_active_features)
        self.renv.lifecycle.mark_after(Lifecycle.CATEGORY_CREATE, cat_name)
      else:
        # If the category is active and singular we cannot enable more features in it
        if cat_desc.singular and cat_inst.get_active_features():
          # If the category or one of its features were requested explicityly we need to nofity user
          if cat_name in features or set(cat_active_features) & set(features):
            raise StopException(
                StopException.EFTR,
                str(
                    "Cannot activate feature '{}', since its category '{}' supports only " +
                    "one active feature at a time").format(cat_active_features[0], cat_name))
          # otherwise we can just continue
          else:
            continue
        cat_inst.activate_features(cat_active_features)

    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_ACTIVATION)

    return feat_order, requested_ftrs

#-API---------------------------------------------------------------------------

  def register_feature_category_class(self, cat_name, cat_class=FeatureCategory,\
      features=None, defaults=None, requires=None, singular=True, always=True):
    self.categories[cat_name] = \
        CategoryDesc(cat_name, cat_class, features, defaults, requires, singular, always)
    for feat_name in features:
      self.feature_to_category[feat_name] = cat_name

  def register_feature_class(self, feat_name, feature_class):
    self.features[feat_name] = FeatureDesc(feat_name, feature_class, None)

  def activate(self):
    return self.activate_features(self.renv.get_project_features())

  def deactivate(self):
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_DEACTIVATION)
    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_DEACTIVATION)

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
