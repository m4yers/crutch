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

from crutch.core.services import FeatureJinja
from crutch.core.features import Feature, FeatureCategory
from crutch.core.runner import Runner


class FeatureNew(Feature):

  def __init__(self, renv):
    self.jinja_ftr = renv.feature_ctrl.get_active_feature('jinja')
    super(FeatureNew, self).__init__(renv)

  def register_properties(self):
    super(FeatureNew, self).register_properties()
    renv = self.renv

    project_directory = renv.get_prop('project_directory')

    renv.set_prop('user_name', renv.get_prop('os_login'), True, True)
    renv.set_prop('project_type', renv.get_prop('project_type'), True, True)
    renv.set_prop(
        'project_name',
        renv.get_prop('project_name') or os.path.basename(project_directory), True, True)
    # Remove ourselves from the list
    renv.set_prop(
        'project_features',
        renv.get_prop('project_features')[1:] or 'default', mirror_to_config=True)

  def handle(self):
    renv = self.renv
    # jenv = renv.jenv

    project_type = renv.get_project_type()
    project_directory = renv.get_project_directory()

    # We need to activate features for the current project type, since we are
    # already within a `new` feature runner we create type specific runner
    # explicitly and activate its features `manually`. This activation will
    # usually lead to creation of new feature specific replacements used by
    # jinja template render
    renv.runners.get(project_type)(renv).activate_features()

    folders = ['main'] + ['features' + os.path.sep + f for f in renv.get_project_features()]

    for folder in folders:
      self.jinja_ftr.copy_folder(
          os.path.join(project_type, folder),
          project_directory)


class RunnerNew(Runner):

  def __init__(self, renv):
    super(RunnerNew, self).__init__(renv)

    self.register_feature_category_class(
        'services',
        FeatureCategory,
        features=['jinja'],
        defaults=['jinja'])
    self.register_feature_class('jinja', FeatureJinja)

    self.register_feature_category_class(
        'crutch',
        FeatureCategory,
        features=['new'],
        defaults=['new'],
        requires=['jinja'])
    self.register_feature_class('new', FeatureNew)

  def run(self):
    """
    Before we run anything we save all the features passed from cli and replace
    them with simple 'default' value so the feature-ctrl will initialize `new`
    the way we need
    """
    saved_features = self.renv.get_prop('project_features')
    self.renv.set_prop('project_features', 'default')

    #---------------------------
    renv = self.renv
    self.activate_features()
    #---------------------------

    self.renv.set_prop('project_features', saved_features)

    #---------------------------
    self.invoke_feature(renv.get_run_feature())
    #---------------------------
