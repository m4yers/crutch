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

from crutch.core.exceptions import StopException
from crutch.core.features.basics import FeatureCategory
from crutch.core.replacements import GenerativeReplacementsProvider

class CategoryDesc(object):

  def __init__(self, name, init, features, defaults, requires,\
      singular, always):
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
      for ftr_name in cat_inst.get_active_feature_names():
        self.data['project_feature_' + ftr_name] = True
    return self.data


class FeatureCtrl(object):

  def __init__(self, renv):
    self.renv = renv

    self.dep_graph = nx.DiGraph()
    self.features = dict()
    self.feature_to_category = dict()

    self.categories = dict()
    self.active_categories = dict()

    renv.repl.add_provider('feature-ctrl-repl', FeatureCtrlReplProvider(renv))

  def __repr__(self):
    result = 'FEATURE CTRL' + os.linesep + os.linesep
    for cat_name, cat in self.categories.items():
      result += ' '
      if cat_name in self.active_categories:
        result += '!'
      result += cat_name + os.linesep + '['
      for ftr_name in cat.features:
        result += ftr_name + ' '
      result += ']' + os.linesep

    return result

#-SUPPORT-----------------------------------------------------------------------

  def is_category(self, name):
    return name in self.categories

  def is_feature(self, name):
    return name in self.features

  def get_category_and_features(self, dep):
    dep_cat_name = None
    req_cat_feat = list()

    if self.is_category(dep):
      dep_cat_name = dep
      req_cat_feat.extend(self.categories[dep].defaults)
    elif self.is_feature(dep):
      dep_cat_name = self.feature_to_category[dep]
      req_cat_feat.append(dep)
    else:
      raise Exception('Requirement {} is not provided'.format(dep))

    return dep_cat_name, req_cat_feat

  def flatten_features(self, features):
    """
    If `features` is a `string` equal to `default` collect all default features
    of all categories. If it is a `list` containing category name, replace
    those with default features of that category. Features names are preserved.

    :param features: `list` of feature(category) names or `string` default
    """
    result = list()

    if features == 'default':
      result.extend(sum([d.defaults for d in self.categories.values()], []))

    elif features:
      for name in features:
        if self.is_category(name):
          result.extend(self.categories[name].defaults)
        elif self.is_feature(name):
          result.append(name)

    return set(result)

  def get_features_dependency_closure(self, features):
    """
    Return iterative dependency closure of the `features` list. Note, since
    dependency graph can contain categories, the result may contain categories
    too.

    :param features: `iterable` of feature names
    :return: `set` containing iterative dependency closure of `features`. May
      contain category names.
    """
    closure = set(features)

    while True:
      new = closure | set(sum(map(self.dep_graph.predecessors, closure), []))
      if closure == new:
        break
      closure = new

    return closure

  def get_init_order(self, features):
    """
    Derive feature instantiation order from the dependency graph.

    :param features: `iterable` of feature names
    :returns: total instantiation order which may include categories that
    require a special handling; also it returns flatten view of the requested
    features in instantiating order.
    """
    flatten = self.flatten_features(features)
    closure = self.get_features_dependency_closure(flatten)

    subgraph = self.dep_graph.subgraph(closure)
    total_order = list(nx.topological_sort(subgraph))
    flatten_order = [f for f in total_order if f in flatten]

    return total_order, flatten_order

  def get_singularity_conflicts(self, features):
    """
    Return category/feature conflicts if any, where more than one feature
    belongs to the same singlular category.

    :param features: `list` of feature names.
    :returns: True if there are no conflicts.
    """

    for cat_desc in self.categories.values():
      if cat_desc.singular:
        intersection = set(cat_desc.features) & set(features)
        if len(intersection) > 1:
          yield cat_desc.name, intersection

  def get_activation_conflicts(self, features):
    """
    Verify whether the `features` does not contain conflicting features, that
    is features of a singular category that is active and has other active
    features.

    :param features: `list` of feature names.
    :returns: True if there are no conflicts.
    """

    for ftr_name in features:
      cat_name = self.feature_to_category[ftr_name]
      cat_inst = self.active_categories.get(cat_name, None)

      if cat_inst and not cat_inst.is_active_feature(ftr_name):
        yield cat_name, ftr_name

  def clean_up_total_order(self, order):
    """
    Total instantiation order may contain categories which results in two
    cases:
      - Case 1: There are features in that total order that belong to the
        category, and we simply remove this category from the list, this at
        least one feature of this category will be instantiated.
      - Case 2: There are no features in that total order that belong to the
        category, so we need to check the active categories, if this specific
        category is already active we simply remove it from the order,
        otherwise we add its defaults to that order.

    :param order: `iterable` total instantiation order
    :return: cleansed total instantiation order
    """
    result = list()

    for name in order:
      if self.is_category(name):
        cat_desc = self.categories[name]
        if not (set(order) & set(cat_desc.features)):
          cat_inst = self.active_categories.get(name, None)
          if not cat_inst:
            result.extend(cat_desc.defaults)
      else:
        result.append(name)

    return result

  def activate_features(self, request, set_up=False):
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_CREATION)

    total_order, flatten_order = self.get_init_order(request)

    total_order = self.clean_up_total_order(total_order)

    # Check for conflicts within flatten(user requested) order
    conflicts = list()
    for category, features in self.get_singularity_conflicts(flatten_order):
      conflicts.append(
          str("Singular category '{}' cannot have all of '{}' features " +
              "activated at the same time").format(category, features))
    if conflicts:
      raise StopException(
          StopException.EFTR,
          'There were some conflicting dependencies:\n' + '\n'.join(conflicts))

    # Check for total order conflicts relative to already active categories
    conflicts = list()
    for category, feature in self.get_activation_conflicts(total_order):
      # In case the category was requested explicitly we can ignore this
      # conflict, since in this case user requested any feature(default or
      # already enabled) of that category
      if category in request:
        continue

      # Inability to instantiate an explicit request is an error
      if feature in request:
        conflicts.append(
            str("Cannot activate '{}' feature because its category '{}' is " +
                "singular and already contains active features").
            format(feature, category))

    if conflicts:
      raise StopException(
          StopException.EPERM,
          'There were some conflicting dependencies:\n' + '\n'.join(conflicts))

    # Finally instantiate, activate and set up if needed all the features
    for ftr_name in total_order:
      cat_name = self.feature_to_category[ftr_name]
      cat_desc = self.categories[cat_name]
      cat_inst = self.active_categories.get(cat_name, None)

      if not cat_inst:
        cat_inst = cat_desc.init(
            self.renv,
            {n: self.features[n].init for n in cat_desc.features})

        if set_up:
          self.renv.lifecycle.mark_before(Lifecycle.CATEGORY_SET_UP, cat_name)
          cat_inst.set_up()
          self.renv.lifecycle.mark_after(Lifecycle.CATEGORY_SET_UP, cat_name)

        self.renv.lifecycle.mark_before(Lifecycle.CATEGORY_ACTIVATE, cat_name)
        cat_inst.activate()
        self.renv.lifecycle.mark_after(Lifecycle.CATEGORY_ACTIVATE, cat_name)

        self.active_categories[cat_name] = cat_inst

      if not cat_inst.is_active_feature(ftr_name):
        cat_inst.activate_feature(ftr_name)

    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_DESTRUCTION)

    return total_order, flatten_order

  def deactivate_features(self, request, tear_down=False):
    pass

#-API---------------------------------------------------------------------------

  def register_feature_category_class(self, cat_name, \
      cat_class=FeatureCategory, features=None, defaults=None, requires=None,\
      singular=True, always=True):
    self.categories[cat_name] = CategoryDesc(
        cat_name, cat_class, features, defaults, requires, singular, always)
    for ftr_name in features:
      self.feature_to_category[ftr_name] = cat_name

  def register_feature_class(self, ftr_name, feature_class, requires=None):
    cat_name = self.feature_to_category.get(ftr_name, None)
    if not cat_name:
      StopException(
          StopException.EFTR,
          "Category for feature '{}' is not defined".format(ftr_name),
          True)

    self.dep_graph.add_node(ftr_name)

    # NOTE: Dependencies can contain categories

    # Add all category requirements
    cat_desc = self.categories[cat_name]
    for requirement in cat_desc.requires:
      if not self.dep_graph.has_edge(requirement, ftr_name):
        self.dep_graph.add_edge(requirement, ftr_name)

    # Add feature's own requirements
    ftr_desc = FeatureDesc(ftr_name, feature_class, requires)
    for requirement in ftr_desc.requires:
      if not self.dep_graph.has_edge(requirement, ftr_name):
        self.dep_graph.add_edge(requirement, ftr_name)

    if not nx.is_directed_acyclic_graph(self.dep_graph):
      raise Exception(
          'Features you have provided form a circular dependency:\n' +
          list(nx.find_cycle(self.dep_graph, orientation='ignore')))

    self.features[ftr_name] = ftr_desc

  def activate(self):
    try:
      return self.activate_features(self.renv.get_project_features())
    except StopException as stop:
      stop.terminate = True
      raise

  def deactivate(self):
    pass
    # self.deactivate_features(self.renv.get_project_features())

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
