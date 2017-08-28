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

from crutch.core.features.jinja import FeatureJinja
from crutch.core.features.feature import FeatureFeature
from crutch.core.features.new import FeatureNew


class Runners(object):

  def __init__(self, runners):
    self.runners = runners

  def get(self, kind):
    return self.runners.get(kind, Runner)


class Runner(object):

  def __init__(self, renv):
    self.renv = renv
    self.default_run_feature = None

    self.register_feature_category_class(
        'crutch',
        features=['jinja', 'feature', 'new'],
        defaults=['feature'],
        singular=False)
    self.register_feature_class('jinja', FeatureJinja)
    self.register_feature_class('feature', FeatureFeature)
    self.register_feature_class('new', FeatureNew, requires=['jinja'])

  def register_default_run_feature(self, name):
    self.default_run_feature = name

  def register_feature_category_class(self, *args, **kwargs):
    self.renv.feature_ctrl.register_feature_category_class(*args, **kwargs)

  def register_feature_class(self, *args, **kwargs):
    self.renv.feature_ctrl.register_feature_class(*args, **kwargs)

  def activate_features(self):
    return self.renv.feature_ctrl.activate()

  def deactivate_features(self):
    return self.renv.feature_ctrl.deactivate()

  def invoke_feature(self, name):
    self.renv.feature_ctrl.invoke(name)

  def run(self):
    renv = self.renv
    run_feature = renv.get_run_feature() or self.default_run_feature
    renv.lifecycle.mark_before(Lifecycle.RUNNER_RUN, run_feature)
    self.invoke_feature(run_feature)
    renv.lifecycle.mark_after(Lifecycle.RUNNER_RUN, run_feature)
