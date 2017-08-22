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

from crutch.core.exceptions import StopException
from crutch.core.features.basics import Feature, FeatureMenu


NAME = 'feature'
OPT_FEATURE = 'feature_feature_feature'


class FeatureMenuCppFileManager(FeatureMenu):

  def __init__(self, renv, handler_view=None, handler_enable=None, handler_disable=None):
    super(FeatureMenuCppFileManager, self).__init__(renv, NAME, 'Feature Manager')

    self.add_default_action('View all the features', handler_view)

    enable = self.add_action('enable', 'Enable a feature', handler_enable)
    enable.add_argument(dest=OPT_FEATURE, metavar='FEATURE', help='Feature to enable')

    disable = self.add_action('disable', 'Disable a feature', handler_disable)
    disable.add_argument(dest=OPT_FEATURE, metavar='FEATURE', help='Feature to disable')


class FeatureStatus(object):

  def __init__(self, name, desc, active):
    self.name = name
    self.desc = desc
    self.active = active

  def __str__(self):
    return '[Feature {}, active: {}]'.format(self.name, self.active)


class CategoryStatus(object):

  def __init__(self, name, desc, active, features=None):
    self.name = name
    self.desc = desc
    self.active = active
    self.features = features or list()

  def __str__(self):
    result = '[Category {}, active: {}]'.format(self.name, self.active)
    for feature in self.features:
      result += '\n  {}'.format(feature)
    return result


class FeatureFeature(Feature):

  def __init__(self, renv):
    super(FeatureFeature, self).__init__(renv, FeatureMenuCppFileManager(
        renv,
        handler_view=self.action_view,
        handler_enable=self.action_enable,
        handler_disable=self.action_disable))

#-SUPPORT-----------------------------------------------------------------------

  def get_feature_status(self, ftr_name):
    ctrl = self.renv.feature_ctrl
    cat_name = ctrl.feature_to_category[ftr_name]
    cat_inst = ctrl.active_categories.get(cat_name, None)
    return FeatureStatus(
        ftr_name,
        ctrl.features[ftr_name],
        cat_inst != None and ftr_name in cat_inst.get_active_feature_names())

  def get_category_status(self, cat_name):
    ctrl = self.renv.feature_ctrl
    cat_desc = ctrl.categories[cat_name]
    cat_inst = ctrl.active_categories.get(cat_name, None)
    cat_status = CategoryStatus(cat_name, cat_desc, cat_inst != None)
    for ftr_name in cat_desc.features:
      ftr_status = FeatureStatus(
          ftr_name,
          ctrl.features[ftr_name],
          cat_inst != None and ftr_name in cat_inst.get_active_feature_names())
      cat_status.features.append(ftr_status)
    return cat_status

  def get_categories_status(self):
    ctrl = self.renv.feature_ctrl
    return [self.get_category_status(c) for c in ctrl.categories.keys()]

  def get_status(self, name):
    if self.is_category(name):
      return self.get_category_status(name)
    return self.get_feature_status(name)

  def is_category(self, name):
    return self.renv.feature_ctrl.is_category(name)

  def is_feature(self, name):
    return self.renv.feature_ctrl.is_feature(name)


#-ACTIONS-----------------------------------------------------------------------

  def action_view(self):
    print 'FEATURE VIEW:'
    for cat_status in self.get_categories_status():
      print '\n{}'.format(cat_status)

  def action_enable(self):
    renv = self.renv
    ctrl = renv.feature_ctrl
    name = renv.get_prop(OPT_FEATURE)
    status = self.get_status(name)
    if status.active:
      raise StopException(StopException.EFTR, "Feature '{}' already enabled".format(name))
    else:
      _, requested_ftrs = ctrl.activate_features([name])
      user_ftrs = list(set(renv.get_project_features()) | set(requested_ftrs))
      renv.set_prop('project_features', user_ftrs, mirror_to_config=True)

  def action_disable(self):
    renv = self.renv
    ctrl = renv.feature_ctrl
    name = renv.get_prop(OPT_FEATURE)
    status = self.get_status(name)
    if status.active:
      normalized = ctrl.normalize_project_features([name])
      ftr_name = sum(normalized.values(), [])[0]
      project_features = renv.get_project_features()
      # We can only remove an explicit feature, all dependency features won't be in that list,
      # unless feature is explicit and is a dependency at the same time, in this case it is still
      # alright because it will be instantiated next time as an implicit dependency if needed
      if ftr_name in project_features:
        project_features.remove(ftr_name)
        renv.set_prop('project_features', project_features, mirror_to_config=True)
      else:
        raise StopException(
            StopException.EFTR,
            "You cannot disable a feature that is a dependency of another")
    else:
      raise StopException(
          StopException.EFTR,
          "Feature '{}' is not enabled".format(name))
