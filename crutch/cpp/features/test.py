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

import subprocess
import os

from crutch.core.features import create_simple_feature_category
from crutch.core.features import Feature, FeatureMenu

import crutch.cpp.features.build as Build

NAME = 'test'
OPT_CFG = 'feature_test_config'
OPT_GROUP = 'feature_test_group'


class FeatureMenuCppTest(FeatureMenu):

  def __init__(self, renv, name=NAME, handler_default=None, handler_add=None):
    super(FeatureMenuCppTest, self).__init__(renv, name, 'Test C++ Project')
    default = self.add_default_action('Test project', handler_default)
    default.add_argument(
        '-c', '--config', dest=OPT_CFG, metavar='CONFIG',
        default='debug', choices=['debug', 'release'],
        help='Select project config')

    add = self.add_action('add', 'Add test file group', handler_add)
    add.add_argument(dest=OPT_GROUP, metavar='GROUP', help='Group name')


FeatureCategoryCppTest = create_simple_feature_category(FeatureMenuCppTest)


class FeatureCppTest(Feature):

  def __init__(self, renv, name):
    self.name = name
    self.build_ftr = \
        renv.feature_ctrl.get_active_category(Build.NAME).get_active_features()[0]
    super(FeatureCppTest, self).__init__(renv)

  def register_menu(self):
    return FeatureMenuCppTest(
        self.renv,
        self.name,
        handler_default=self.action_default,
        handler_add=self.action_add)

#-SUPPORT-----------------------------------------------------------------------

  def get_build_directory(self):
    renv = self.renv
    test_cfg = renv.get_prop(OPT_CFG)
    suffix = test_cfg if self.build_ftr.is_make() else ''
    return self.build_ftr.get_build_directory(suffix)

  def get_test_src_dir(self):
    return os.path.join(self.renv.get_project_directory(), 'test')

  def get_test_bin_dir(self):
    return os.path.join(self.get_build_directory(), 'test')

  def get_test_names(self):
    path = self.get_test_src_dir()
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

  def run_test(self, name):
    renv = self.renv

    build_dir = self.get_build_directory()
    build_cmk = renv.get_prop(Build.PROP_CMK)
    test_cfg = renv.get_prop(OPT_CFG)

    build = [build_cmk, '--build', build_dir, '--target', name, '--config', test_cfg]
    subprocess.call(' '.join(build), stderr=subprocess.STDOUT, shell=True)

    suffix = test_cfg.capitalize() if self.build_ftr.is_xcode() else ''
    exe = os.path.join(self.get_test_bin_dir(), name, suffix, name)
    subprocess.call(exe, stderr=subprocess.STDOUT, shell=True)

#-ACTIONS-----------------------------------------------------------------------

  def action_default(self):
    renv = self.renv

    build_dir = self.get_build_directory()
    test_cfg = renv.get_prop(OPT_CFG)

    # If the build directory is not present we call build.configure first
    if not os.path.exists(build_dir):
      self.build_ftr.configure(build_dir, test_cfg)

    map(self.run_test, self.get_test_names())

  def action_add(self):
    renv = self.renv

    group = renv.get_prop(OPT_GROUP)
    print group


class FeatureCppTestGTest(FeatureCppTest):

  def __init__(self, renv):
    super(FeatureCppTestGTest, self).__init__(renv, 'gtest')
