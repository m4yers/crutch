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

from crutch.core.features.basics import Feature, FeatureMenu

NAME = 'new'

class FeatureMenuNew(FeatureMenu):

  def __init__(self, renv, handler_default=None):
    super(FeatureMenuNew, self).__init__(renv, NAME, 'Creates new project')

    default = self.add_default_action('View all the features', handler_default)

    default.add_argument(
        dest='project_type', metavar='TYPE',
        choices=['cpp', 'python'], help='Project type')

    default.add_argument(
        '-n', '--name', metavar='NAME', dest='project_name',
        help='Project name(default=basename(FOLDER))')

    default.add_argument(
        '-f', '--features', metavar='FEATURE', nargs='*', default='default',
        dest='project_features', help='Select project features')


class FeatureNew(Feature):

  def __init__(self, renv):
    self.jinja_ftr = renv.feature_ctrl.get_active_feature('jinja')
    super(FeatureNew, self).__init__(renv, FeatureMenuNew(renv, self.create))

  def create(self):
    renv = self.renv

    crutch_directory = renv.get_crutch_directory()
    project_directory = renv.get_project_directory()
    project_features = renv.get_project_features()
    project_type = renv.get_project_type()

    # Create .crutch directory
    os.makedirs(crutch_directory)

    # Mirror some project properties to config
    renv.set_prop(
        'project_username',
        renv.get_prop('project_username') or renv.get_prop('sys_login'),
        mirror_to_config=True)

    renv.set_prop(
        'project_name',
        renv.get_prop('project_name') or os.path.basename(project_directory),
        mirror_to_config=True)

    renv.set_prop('project_type', project_type, mirror_to_config=True)

    # We need to activate features for the current project type, since we are
    # already within a `new` feature runner we create type specific runner
    # explicitly and activate its features `manually`.
    runner = renv.runners.get(project_type)(renv)
    total_order, flatten_order = renv.feature_ctrl.activate_features(
        project_features,
        set_up=True)

    # Save user features to config
    renv.set_prop('project_features', flatten_order, mirror_to_config=True)

    psub = {'ProjectNameRepl': renv.get_project_name()}

    folders = ['main'] + [os.path.join('features', f) for f in total_order]

    for folder in folders:
      self.jinja_ftr.copy_folder(
          os.path.join(project_type, folder),
          project_directory,
          psub)

    print("Done!")

    return runner
