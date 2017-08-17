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

class Feature(object):

  def __init__(self, renv):
    self.renv = renv
    self.dispatcher = {
        'default': self.handle_default
        }

    self.register_actions(self.renv.menu)
    self.register_files()
    self.register_properties()

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
    project_directory = os.path.abspath(self.renv.get_prop('project_directory'))
    self.renv.set_prop('project_directory', project_directory, mirror_to_repl=True)

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

  def get_active_feature_names(self):
    return self.active_features.keys()

  def get_active_features(self):
    return self.active_features.values()

  def set_up(self):
    for feature in self.active_features.values():
      feature.set_up()

  def tear_down(self):
    for feature in self.active_features.values():
      feature.tear_down()

  def handle_features(self):
    for feature in self.active_features.values():
      feature.handle()

  def handle_feature(self, feature_name):
    feature = self.active_features.get(feature_name, None)
    if not feature:
      raise Exception("You cannot handle non-active feature")
    feature.handle()
