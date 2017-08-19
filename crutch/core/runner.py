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


class Runner(object):

  def __init__(self, renv):
    self.renv = renv
    self.default_run_feature = None

  def register_default_run_feature(self, name):
    self.default_run_feature = name

  def register_feature_category_class(self, *args, **kwargs):
    self.renv.feature_ctrl.register_feature_category_class(*args, **kwargs)

  def register_feature_class(self, *args, **kwargs):
    self.renv.feature_ctrl.register_feature_class(*args, **kwargs)

  def activate_features(self):
    return self.renv.feature_ctrl.activate()

  def invoke_feature(self, name):
    self.renv.feature_ctrl.invoke(name)

  def run(self):
    renv = self.renv
    self.invoke_feature(renv.get_run_feature() or self.default_run_feature)
