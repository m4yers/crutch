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

from crutch.core.features.basics import Feature
from crutch.core.runner import Runner


class FeatureNew(Feature):

  def __init__(self, renv):
    self.jinja_ftr = renv.feature_ctrl.get_active_feature('jinja')
    super(FeatureNew, self).__init__(renv)

  def register_properties(self):
    super(FeatureNew, self).register_properties()
    renv = self.renv

    project_directory = renv.get_project_directory()

    renv.set_prop('project_username', renv.get_prop('sys_login'), mirror_to_config=True)
    renv.set_prop('project_type', renv.get_prop('project_type'), mirror_to_config=True)
    renv.set_prop(
        'project_name',
        renv.get_prop('project_name') or os.path.basename(project_directory),
        mirror_to_config=True)

  def handle(self):
    renv = self.renv

    project_type = renv.get_project_type()
    project_directory = renv.get_project_directory()

    # We need to activate features for the current project type, since we are
    # already within a `new` feature runner we create type specific runner
    # explicitly and activate its features `manually`. This activation will
    # usually lead to creation of new feature specific replacements used by
    # jinja template render
    all_ftrs, user_ftrs = renv.runners.get(project_type)(renv).activate_features()

    # User requested features contain 'new' and we need to remove it before
    # mirroring features to config
    user_ftrs.remove('new')

    renv.set_prop('project_features', user_ftrs, mirror_to_config=True)

    folders = ['main'] + ['features' + os.path.sep + f for f in all_ftrs]

    psub = {'ProjectNameRepl': renv.get_project_name()}

    for folder in folders:
      self.jinja_ftr.copy_folder(
          os.path.join(project_type, folder),
          project_directory,
          psub)


class RunnerNew(Runner):

  def __init__(self, renv):
    super(RunnerNew, self).__init__(renv)

    self.register_feature_category_class(
        'crutch',
        features=['new'],
        defaults=['new'],
        requires=['jinja'])
    self.register_feature_class('new', FeatureNew)
