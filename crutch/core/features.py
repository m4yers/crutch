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

from crutch.core.replacements import GenerativeReplacementsProvider

class DefaultFeaturesReplacementsProvider(GenerativeReplacementsProvider):
  """
  Default replacements provider for the Features class. It regenerates all
  replacements every time its owner requests it
  """

  def __init__(self, features):
    GenerativeReplacementsProvider.__init__(self)
    self.features = features

  def generate(self):
    self.data = dict()
    for category in self.features.get_enabled_categories():
      self.data['project_has_feature_category_' + category] = True
    for feature in self.features.get_enabled_features():
      self.data['project_has_feature_' + feature] = True
    return self.data

class Category(object):
  def __init__(self, name, features, default, only_one):
    self.name = name
    self.features = features
    self.default = default
    self.only_one = only_one


class Features(object):
  """
  Default runner features representation class
  """

  def __init__(self):
    # category name -> category object map
    self.categories = dict()

    # category name -> selected features list map
    self.parsed = dict()

    # feature name -> category object map
    self.features = dict()

  def __repr__(self):
    enabled = {True: '+', False: '-'}
    default = {True: '!', False: ''}

    features = list()

    for name, category in self.categories.items():
      if name not in self.parsed:
        continue

      decorated_features = [
          '{1}{0}{2}'.format(feature, \
              enabled.get(feature in self.parsed[name]), \
              default.get(feature in category.default)) \
              for feature in category.features]

      features.append('{}: {}'.format(name, ', '.join(decorated_features)))

    return '[{} {}]'.format(self.__class__.__name__, ', '.join(features))

  def get_repl_provider(self):
    return DefaultFeaturesReplacementsProvider(self)

  def get_feature_one(self, category):
    features = self.get_enabled_features(category)
    return features[0] if features else ''

  def add_category(self, name, features, default, only_one):
    if self.categories.has_key(name):
      raise Exception("Category already exists")

    category = Category(name, features, default, only_one)

    self.categories[name] = category
    self.parsed[name] = default

    for feature in features:
      self.features[feature] = category

  def parse(self, features):
    self.parsed = dict()

    for feature in features:
      category = self.features.get(feature)
      if not category:
        raise Exception("Cannot find the feature '%s'" % feature)

      parsed = self.parsed.get(category.name, [])

      if category.only_one and parsed:
        raise Exception("Feature overlap '%s' with '%s'" % feature, parsed)

      parsed.append(feature)

      self.parsed[category.name] = parsed

  def get_enabled_features(self, category=None):
    if category:
      return self.parsed.get(category, [])
    return sum(self.parsed.values(), [])

  def get_enabled_categories(self):
    return self.parsed.keys()


class Feature(object):

  def __init__(self, renv):
    self.renv = renv
    self.dispatcher = {
        'default': self.handle_default
        }

    self.register_actions(self.renv.menu)
    self.register_files()
    self.register_properties()
    self.register_replacemets()

  def register_actions(self, menu):
    pass

  def register_files(self):
    """
    Here you add your feature files and folders, so they can be removed if
    a programmer decides to remove the feature. Also you may register any temp
    files or directories so `clean` feature may remove them
    """
    pass

  def register_properties(self):
    pass

  def register_replacemets(self):
    pass

  def register_handler(self, action, handler):
    self.dispatcher[action] = handler

  def handle_default(self):
    print '{} default action is not set'.format(self.__class__.__name__)

  def set_up(self):
    """
    Set up is called when a new feature is added during `new` invokation or
    afterwards using `feature` feature
    """
    pass

  def tear_down(self):
    """
    Tear down is called when a feature is removed by `feature` feature
    """
    pass

  def handle(self):
    """
    This method is invoked to handle feature invokation
    """
    action = self.renv.get_prop('action')
    self.dispatcher.get(action)()


class FeatureCategory(Feature):

  def __init__(self, renv, features):
    super(FeatureCategory, self).__init__(renv)
    self.features = features
    self.active_features = dict()

  def activate_features(self, feature_names):
    map(self.activate_feature, feature_names)

  def activate_feature(self, feature_name):
    instance = self.features[feature_name](self.renv)
    self.active_features[feature_name] = instance

  def deactivate_feature(self, feature_name):
    feature = self.active_features.get(feature_name, None)
    if not feature:
      raise Exception("You cannot deactivate non-active feature")
    feature.tear_down()
    del self.active_features[feature_name]

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
