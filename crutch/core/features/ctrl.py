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

from more_itertools import unique_everseen

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

    self.dep_graph = nx.DiGraph()
    self.features = dict()
    self.feature_to_category = dict()
    self.features_in_activation_process = None

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

    :param request: `list` of feature(category) names or `string` default
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

    :param request: `list` of feature(category) names or `string` default
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
          # We eagerly add every dependency of the defaults, later we will
          # remove duplicates
          total_order, _ = self.get_deactivation_order(
              set(cat_inst.get_active_feature_names()) - set(order))
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
          "Names '{}' are not features nor categories".format(errors))

    flatten = self.flatten_with_defaults(request)
    closure = self.get_features_dependency_closure(flatten)

    total_order = self.get_topological_order(closure)
    total_order = self.clean_up_activation_order(total_order)
    flatten_order = [f for f in total_order if f in flatten]

    return total_order, flatten_order

  def get_deactivation_order(self, request):
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
          "Names '{}' are not features nor categories", format(errors))

    flatten = self.flatten_with_active(request)

    closure = set(flatten)
    while True:
      new = closure | set(self.get_features_dependency_closure(closure))
      if closure == new:
        break
      closure = new

    total_order = self.get_reversed_topological_order(closure)
    total_order = self.clean_up_deactivation_order(total_order)
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
    :returns: (cat_name, ftr_name) `iterator` if there are conflicts
    """

    for ftr_name in features:
      cat_name = self.feature_to_category[ftr_name]
      cat_desc = self.categories[cat_name]
      cat_inst = self.active_categories.get(cat_name, None)

      if cat_inst and cat_desc.singular:
        yield cat_name, ftr_name

  def activate_features(self, request, set_up=False):
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_CREATION, request)

    total_order, flatten_order = self.get_activation_order(request)

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
        conflicts.append(
            "Category '{}' is already active".format(category))

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
          cat_name = self.feature_to_category[ftr_name]
          cat_inst = self.active_categories.get(cat_name, None)
          if cat_inst.is_active_feature(ftr_dep):
            yield ftr_name, ftr_dep

  def deactivate_features(self, request, tear_down=False, skip=None):
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_DESTRUCTION, request)

    total_order, flatten_order = self.get_deactivation_order(request)

    print 'request: {}'.format(request)
    print 'total: {}'.format(total_order)
    print 'flatten: {}'.format(flatten_order)

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
      if skip and ftr_name in skip:
        continue

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

        del self.categories[cat_name]

    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_DESTRUCTION, total_order)

    return total_order, flatten_order

  def check_dependency(self, ftr_name, dep_name):
    cat_name = self.feature_to_category[ftr_name]

    if self.is_category(dep_name) and dep_name == cat_name:
      raise StopException(
          StopException.EPERM,
          "It is forbidden to have self-dependency. Check category '{}'".
          format(dep_name))

    # elif self.is_feature(dep_name):
    #   dep_cat_name = self.feature_to_category[dep_name]
    #   if dep_cat_name == cat_name:
    #     raise StopException(
    #         StopException.EPERM,
    #         str("It is forbidden to have dependencies within one category." +
    #             " Check features '{}'").format((ftr_name, dep_name)))

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
    for dep_name in cat_desc.requires:
      self.check_dependency(ftr_name, dep_name)
      if not self.dep_graph.has_edge(dep_name, ftr_name):
        self.dep_graph.add_edge(dep_name, ftr_name)

    # Add feature's own requirements
    ftr_desc = FeatureDesc(ftr_name, feature_class, requires)
    for dep_name in ftr_desc.requires:
      self.check_dependency(ftr_name, dep_name)
      if not self.dep_graph.has_edge(dep_name, ftr_name):
        self.dep_graph.add_edge(dep_name, ftr_name)

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
    self.deactivate_features('all')

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
