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

import logging
import uuid
import os

import networkx as nx

from more_itertools import unique_everseen

import crutch.core.lifecycle as Lifecycle

from crutch.core.exceptions import StopException
from crutch.core.features.basics import FeatureCategory
from crutch.core.replacements import GenerativeReplacementsProvider

LOGGER = logging.getLogger(__name__)
SINK_CATEGORY = 'sink_category_{}'.format(uuid.uuid1())

class CategoryDesc(object):

  def __init__(self, name, init, features, defaults, requires, mono):
    self.name = name
    self.init = init
    self.features = features or list()
    self.defaults = defaults or list()
    self.requires = requires or list()
    self.mono = mono


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
    ctrl = self.renv.feature_ctrl

    # Add already active features/categories
    for cat_name, cat_inst in ctrl.active_categories.items():
      self.data['project_feature_category_' + cat_name] = True
      for ftr_name in cat_inst.get_active_feature_names():
        self.data['project_feature_' + ftr_name] = True

    # Add features and categoires to be activated if any
    if ctrl.features_in_activation_process:
      for ftr_name in ctrl.features_in_activation_process:
        cat_name = ctrl.feature_to_category[ftr_name]
        self.data['project_feature_category_' + cat_name] = True
        self.data['project_feature_' + ftr_name] = True

    return self.data


class FeatureCtrl(object):

  def __init__(self, renv):
    self.renv = renv
    self.dep_graph = nx.DiGraph() # it is more like a forest of trees
    self.features = dict()
    self.feature_to_category = dict()
    self.features_in_activation_process = None
    self.sink_category_name = uuid.uuid1()
    self.sink_category = CategoryDesc(
        self.sink_category_name, FeatureCategory, [], [], [], False)
    self.categories = {self.sink_category_name : self.sink_category}
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

  def get_topological_order(self, request):
    subgraph = self.dep_graph.subgraph(request)
    return list(nx.topological_sort(subgraph))

  def get_reversed_topological_order(self, request):
    subgraph = self.dep_graph.subgraph(request).reverse()
    return list(nx.topological_sort(subgraph))

  def get_name_errors(self, names):
    """
    Yield names that are not categories nor features.

    :param names: `list` of names to check
    """
    for name in names:
      if not self.is_category(name) and not self.is_feature(name):
        yield name

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

  def flatten_with_defaults(self, request):
    """
    Replace every category name in `request` `list` with this category's
    default feature list

    :param request: `list` of feature(category) names
    """
    result = list()

    for name in request:
      if self.is_category(name):
        result.extend(self.categories[name].defaults)
      elif self.is_feature(name):
        result.append(name)

    return set(result)

  def flatten_with_active(self, request):
    """
    Replace every category name in `request` `list` with this category's
    active feature list

    :param request: `list` of feature(category) names
    """
    result = list()
    for name in request:
      if self.is_category(name):
        cat_inst = self.active_categories.get(name)
        if cat_inst:
          result.extend(cat_inst.get_active_feature_names())
      else:
        result.append(name)
    return result

  def clean_up_activation_order(self, order):
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
        present = set(order) & set(cat_desc.features)
        # We eagerly add every dependency, later we will remove duplicates
        if present:
          total_order, _ = self.get_activation_order(present)
          result.extend(total_order)
        elif name not in self.active_categories.keys():
          total_order, _ = self.get_activation_order(cat_desc.defaults)
          result.extend(total_order)
      else:
        result.append(name)

    return list(unique_everseen(result))

  def clean_up_deactivation_order(self, order):
    """
    Total deactivation order may contain categories that must be flatten into
    active features.

    :param order: `iterable` total deactivation order
    :return: cleansed total deactivation order
    """
    result = list()
    for name in order:
      if self.is_category(name):
        cat_inst = self.active_categories.get(name, None)
        if cat_inst:
          # We eagerly add every active dependency, later we will remove
          # duplicates
          total_order, _ = self.get_deactivation_order(
              cat_inst.get_active_feature_names())
          result.extend(total_order)
      else:
        result.append(name)
    return list(unique_everseen(result))

  def get_activation_order(self, request):
    """
    Derive feature activation order from the dependency graph.

    :param request: `iterable` of feature and categories names
    :returns: total activation order.
    """

    if request == 'default':
      request = sum([d.defaults for d in self.categories.values()], [])

    errors = list(self.get_name_errors(request))
    if errors:
      raise StopException(
          StopException.EFTR,
          "Names {} are not features nor categories".format(errors))

    flatten = self.flatten_with_defaults(request)
    closure = self.get_features_dependency_closure(flatten)

    total_order = self.get_topological_order(closure)
    total_order = self.clean_up_activation_order(total_order)
    flatten_order = [f for f in total_order if f in flatten]

    return total_order, flatten_order

  def get_deactivation_order(self, request, skip):
    """
    Derive feature deactivation order from the dependency graph.

    :param request: `iterable` of feature and categories names
    :returns: total deactivation order.
    """
    if request == 'all':
      request = self.categories.keys()

    errors = list(self.get_name_errors(request))
    if errors:
      raise StopException(
          StopException.EFTR,
          "Names {} are not features nor categories".format(errors))

    flatten = self.flatten_with_active(request)

    closure = set(flatten)
    while True:
      new = closure | set(self.get_features_dependency_closure(closure))
      if closure == new:
        break
      closure = new

    if skip:
      for name in skip:
        if name in closure:
          closure.remove(name)

    # Remove implicit dependencies if some other feature that we won't remove
    # depends on it
    for implicit in [f for f in closure if f not in flatten]:
      for ftr_dep in self.dep_graph.successors(implicit):
        if ftr_dep not in closure:
          cat_name = self.feature_to_category[ftr_dep]
          cat_inst = self.active_categories.get(cat_name, None)
          if cat_inst and cat_inst.is_active_feature(ftr_dep):
            closure.remove(implicit)
            break

    total_order = self.get_reversed_topological_order(closure)
    total_order = self.clean_up_deactivation_order(total_order)
    flatten_order = [f for f in total_order if f in flatten]

    return total_order, flatten_order

  def get_mono_conflicts(self, features):
    """
    Return category/feature conflicts if any, where more than one feature
    belongs to the same mono category.

    :param features: `list` of feature names.
    :returns: True if there are no conflicts.
    """

    for cat_desc in self.categories.values():
      if cat_desc.mono:
        intersection = set(cat_desc.features) & set(features)
        if len(intersection) > 1:
          yield cat_desc.name, intersection

  def get_activation_conflicts(self, features):
    """
    Verify whether the `features` does not contain conflicting features, that
    is features of a mono category that is active and has other active
    features.

    :param features: `list` of feature names.
    :returns: (cat_name, ftr_name) `iterator` if there are conflicts
    """

    for ftr_name in features:
      cat_name = self.feature_to_category[ftr_name]
      cat_desc = self.categories[cat_name]
      cat_inst = self.active_categories.get(cat_name, None)

      if cat_inst and cat_desc.mono:
        yield cat_name, ftr_name

  def activate_features(self, request, set_up=False):
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_CREATION, request)

    total_order, flatten_order = self.get_activation_order(request)

    LOGGER.info("Request: '%s'", request)
    LOGGER.info("Total order: '%s'", total_order)
    LOGGER.info("Flatten order: '%s'", flatten_order)

    # Check for conflicts within flatten(user requested) order
    conflicts = list()
    for category, features in self.get_mono_conflicts(flatten_order):
      conflicts.append(
          str("Mono category '{}' cannot have all of '{}' features " +
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
        conflicts.append(
            "Category '{}' is already active".format(category))

      # Inability to instantiate an explicit request is an error
      if feature in request:
        conflicts.append(
            str("Cannot activate '{}' feature because its category '{}' is " +
                "mono and already contains active features").
            format(feature, category))

    if conflicts:
      raise StopException(
          StopException.EPERM,
          'There were some conflicting dependencies:\n' + '\n'.join(conflicts))

    self.features_in_activation_process = list(total_order)

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
        cat_inst.activate_feature(ftr_name, set_up=set_up)

    self.features_in_activation_process = None

    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_CREATION, total_order)

    return total_order, flatten_order

  def get_deactivation_conflicts(self, features):
    """
    Verify that features about to be removed are not dependencies to other
    features that will stay

    :param features: `list` of feature names.
    :returns: (ftr_name, ftr_dep) `iterator` if there are conflicts
    """
    for ftr_name in features:
      for ftr_dep in self.dep_graph.successors(ftr_name):
        if ftr_dep not in features:
          cat_name = self.feature_to_category[ftr_dep]
          cat_inst = self.active_categories.get(cat_name, None)
          if cat_inst and cat_inst.is_active_feature(ftr_dep):
            yield ftr_name, ftr_dep

  def deactivate_features(self, request, tear_down=False, skip=None):
    """
    Deactivate features and/or categories.

    :param request: `list` of categories and/or features to deactivate; or a
      `str` equal to `all` which means deactivate all active features and
      categories.
    :param tear_down: If `True` every deactivated feature/category will be torn
      down, meaning it will be completely removed from the project.
    :param skip: `list` of feature names to skip during deactivation. Since
      this control has no knowledge of actual project features(it only manages
      dependencies, explicit and implicit), to remove a feature with its
      dependencies you want to skip those features that are explicitly enabled
      by user; otherwise the whole dependency tree will be removed unless some
      other feature depends on some of its sub-trees.
    """
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_DESTRUCTION, request)

    total_order, flatten_order = self.get_deactivation_order(request, skip)

    LOGGER.info("Request: '%s'", request)
    LOGGER.info("Total order: '%s'", total_order)
    LOGGER.info("Flatten order: '%s'", flatten_order)
    LOGGER.info("Skip: '%s'", skip)

    # Before we remove anything we verify if we can do that without breaking
    # any dependencies
    conflicts = list()
    for ftr_name, ftr_dep in self.get_deactivation_conflicts(total_order):
      conflicts.append(
          str("Cannot deactivate feature '{}' because it is a direct " +
              "dependency of '{}'").format(ftr_name, ftr_dep))
    if conflicts:
      raise StopException(
          StopException.EPERM,
          'There were some conflicting dependencies:\n' + '\n'.join(conflicts))

    for ftr_name in total_order:
      cat_name = self.feature_to_category[ftr_name]
      cat_inst = self.active_categories.get(cat_name, None)

      if cat_inst and cat_inst.is_active_feature(ftr_name):
        cat_inst.deactivate_feature(ftr_name, tear_down)

        if cat_inst.get_active_features():
          continue

        self.renv.lifecycle.mark_before(Lifecycle.CATEGORY_DEACTIVATE, cat_name)
        cat_inst.deactivate()
        self.renv.lifecycle.mark_after(Lifecycle.CATEGORY_DEACTIVATE, cat_name)

        if tear_down:
          self.renv.lifecycle.mark_before(
              Lifecycle.CATEGORY_TEAR_DOWN, cat_name)
          cat_inst.tear_down()
          self.renv.lifecycle.mark_after(Lifecycle.CATEGORY_TEAR_DOWN, cat_name)

        del self.active_categories[cat_name]

    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_DESTRUCTION, total_order)

    return total_order, flatten_order

  def assert_category_has_defaults(self, name):
    cat_desc = self.categories[name]
    if not cat_desc.defaults:
      raise StopException(
          StopException.EFTR,
          str("You cannot add dependency on category '{}' because it " +
              "does not have default features defined").format(name))

  def assert_dependency(self, name, dependency):
    if name == dependency:
      raise StopException(
          StopException.EPERM,
          "You cannot add self-dependency for '{}'".format(name))

    if self.is_category(dependency):
      self.assert_category_has_defaults(dependency)
    elif not self.is_feature(dependency):
      raise StopException(
          StopException.EFTR, "Unknown dependency name '{}'".format(dependency))

#-API---------------------------------------------------------------------------

  def register_feature_category_class(
      self, cat_name, cat_class=FeatureCategory, features=None, defaults=None, \
      requires=None, mono=True):
    """
    Register feature category. Every name mentioned in its configuration must
    be previously registered to prevent potential circular dependencies.

    :param cat_name: unique category name
    :param cat_class: category's constructor
    :param features: `list` of feature names this category contains. Feature
      must be previous registered. These feature names must be previously
      registered.
    :param defaults: `list` of default features this category provides if its
      name mentioned as a dependency if none of its features is already active.
    :param requires: `list` of features and/or categories this category depends
      upon. These names must be previously registered.
    :param mono: If `True` this category can have only one active feature at a
      time, otherwise it can have many.
    """
    if not features:
      raise StopException(
          StopException.EFTR,
          "You need to define features list for '{}'".format(cat_name))

    self.categories[cat_name] = CategoryDesc(
        cat_name, cat_class, features, defaults, requires, mono)

    self.dep_graph.add_node(cat_name)

    for ftr_name in features:
      self.assert_dependency(cat_name, ftr_name)

      if self.feature_to_category[ftr_name] != self.sink_category_name:
        raise StopException(
            StopException.EPERM,
            "A feature '{}' cannot be attached to multiple categoires"
            .format(ftr_name))

      if requires:
        for dep_name in requires:
          self.assert_dependency(cat_name, dep_name)
          self.assert_dependency(ftr_name, dep_name)
          if not self.dep_graph.has_edge(dep_name, ftr_name):
            self.dep_graph.add_edge(dep_name, ftr_name)

      self.feature_to_category[ftr_name] = cat_name
      self.sink_category.features.remove(ftr_name)

  def register_feature_class(self, ftr_name, ftr_class, requires=None):
    """
    Register feature. Every name mentioned in its configuration must be
    previously registered to prevent potential circular dependencies. Each
    registered feature is added to a default `sink` category, once you've
    used this feature's name while defining a category it will be attached
    to this category.

    :param ftr_name: unique feature name
    :param ftr_class: feature's constructor
    :param requires: `list` of features and/or categories this feature depends
      upon. These names must be previously registered.
    """
    ftr_desc = FeatureDesc(ftr_name, ftr_class, requires)

    self.dep_graph.add_node(ftr_name)

    if requires:
      self.dep_graph.add_node(ftr_name)
      ftr_desc = FeatureDesc(ftr_name, ftr_class, requires)
      for dep_name in ftr_desc.requires:
        self.assert_dependency(ftr_name, dep_name)
        if not self.dep_graph.has_edge(dep_name, ftr_name):
          self.dep_graph.add_edge(dep_name, ftr_name)

    self.features[ftr_name] = ftr_desc
    self.feature_to_category[ftr_name] = self.sink_category_name
    self.sink_category.features.append(ftr_name)

  def activate(self):
    try:
      return self.activate_features(self.renv.get_project_features())
    except StopException as stop:
      stop.terminate = True
      raise

  def deactivate(self):
    self.deactivate_features('all')

  def invoke(self, feature):
    category = self.active_categories.get(feature, None)
    if category:
      category.handle()
      return

    cat_name = self.feature_to_category[feature]
    self.active_categories[cat_name].handle_feature(feature)

  def get_active_categories_names(self):
    return self.active_categories.keys()

  def get_active_categories(self):
    return self.active_categories.values()

  def get_active_category(self, name):
    assert name in self.active_categories
    return self.active_categories[name]

  def get_active_features_names(self):
    return sum([c.get_active_feature_names() for c \
        in self.get_active_categories()], [])

  def get_active_features(self):
    return sum([c.get_active_features() for c \
        in self.get_active_categories()], [])

  def get_active_feature(self, name):
    cat_name = self.feature_to_category[name]
    assert cat_name in self.active_categories
    cat = self.active_categories[cat_name]
    return cat.get_active_feature(name)

  def get_singular_active_feature(self, cat_name):
    assert cat_name in self.active_categories
    cat = self.active_categories[cat_name]
    return cat.get_active_features()[0]
