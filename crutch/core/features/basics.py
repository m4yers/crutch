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

import crutch.core.lifecycle as Lifecycle


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

  def __init__(self, renv, menu=None):
    self.renv = renv
    self.menu = menu

  def activate(self):
    """
    Activation actions done by a feature or category. This is called during
    feature or category construction
    """
    pass

  def deactivate(self):
    """
    Deactivation actions done by a feature or category. This is called during
    feature or category destruction upon CRUTCH exit
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

  def handle(self):
    action = self.renv.get_prop('action')
    self.menu.handlers.get(action)()


class FeatureCategory(FeatureProto):
  """
  Feature category collects(usually) several features under a single name and
  can act as an interface for them exposing a common menu set. Every feature
  can be called separately as well.
  """

  def __init__(self, renv, features, menu=None):
    super(FeatureCategory, self).__init__(renv, menu)
    self.features = features
    self.active_features = dict()

  def activate_features(self, feature_names):
    map(self.activate_feature, feature_names)

  def activate_feature(self, feature_name):
    if feature_name in self.active_features:
      return
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_CREATE, feature_name)
    instance = self.features[feature_name](self.renv)
    self.active_features[feature_name] = instance
    instance.activate()
    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_CREATE, feature_name)

  def deactivate_feature(self, feature_name):
    self.renv.lifecycle.mark_before(Lifecycle.FEATURE_DESTROY, feature_name)
    feature = self.active_features.get(feature_name, None)
    if not feature:
      raise Exception("You cannot deactivate non-active feature")
    feature.deactivate()
    del self.active_features[feature_name]
    self.renv.lifecycle.mark_after(Lifecycle.FEATURE_DESTROY, feature_name)

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
    def __init__(self, renv, features):
      super(SimpleFeatureCategoryWithMenu, self).__init__(renv, features, menu(renv))
  return SimpleFeatureCategoryWithMenu
