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


class FeatureFeature(Feature):

  def __init__(self, renv):
    super(FeatureFeature, self).__init__(renv)
    self.ctrl = renv.feature_ctrl

  def register_menu(self):
    return FeatureMenuCppFileManager(
        self.renv,
        handler_view=self.action_view,
        handler_enable=self.action_enable,
        handler_disable=self.action_disable)

#-ACTIONS-----------------------------------------------------------------------

  def action_view(self):
    print 'HERE'

  def action_enable(self):
    pass

  def action_disable(self):
    pass
