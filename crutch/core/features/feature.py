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


class FeatureDesc(object):

  def __init__(self, name, enabled):
    self.name = name
    self.enabled = enabled

  def __str__(self):
    return '[Feature {}, active: {}]'.format(self.name, self.enabled)


class CategoryDesc(object):

  def __init__(self, name, enabled, features=None):
    self.name = name
    self.enabled = enabled
    self.features = features or list()

  def __str__(self):
    result = '[Category {}, active: {}]'.format(self.name, self.enabled)
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

  def get_feature_status(self):
    ctrl = self.renv.feature_ctrl
    result = list()
    for cat_name, cat in ctrl.categories.items():
      cat_instance = ctrl.active_categories.get(cat_name, None)
      cat_desc = CategoryDesc(cat_name, cat_instance != None)
      for ftr_name in cat.features:
        ftr_desc = FeatureDesc(
            ftr_name,
            cat_instance != None and ftr_name in cat_instance.get_active_feature_names())
        cat_desc.features.append(ftr_desc)
      result.append(cat_desc)
    return result

#-ACTIONS-----------------------------------------------------------------------

  def action_view(self):
    status = self.get_feature_status()
    print 'FEATURE VIEW:'
    for cat_desc in status:
      print '\n{}'.format(cat_desc)

  def action_enable(self):
    pass

  def action_disable(self):
    pass
