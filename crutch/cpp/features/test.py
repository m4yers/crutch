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

from crutch.core.features import FeatureCategory, FeatureMenu

import crutch.cpp.features.build as Build

NAME = 'test'
OPT_CFG = 'feature_test_default_config'

class FeatureCategoryCppTest(FeatureCategory):

  def __init__(self, renv, features, name=NAME):
    self.name = name
    super(FeatureCategoryCppTest, self).__init__(renv, features)

  def register_actions(self):
    menu = FeatureMenu(self.renv, self.name, 'Test C++ project')

    default = menu.add_default_action('Run tests')
    default.add_argument(
        '-c', '--config', dest='config', metavar='CONFIG',
        default='debug', choices=['debug', 'release'],
        help='Select test config')

    add = menu.add_action('add', 'Add test file group')
    add.add_argument(dest='group', metavar='GROUP', help='Group name')

  def get_build_cat(self):
    return self.renv.feature_ctrl.get_active_category(Build.NAME)

  def get_build_ftr(self):
    return self.get_build_cat().get_active_features()[0]

  def get_build_directory(self):
    renv = self.renv
    test_cfg = renv.get_prop(OPT_CFG)
    build_cat = self.get_build_cat()
    build_ftr = build_cat.get_active_feature_names()
    suffix = test_cfg if 'make' in build_ftr else ''
    return build_cat.get_build_directory(suffix)

  def get_test_src_dir(self):
    return os.path.join(self.renv.get_project_directory(), 'test')

  def get_test_bin_dir(self):
    return os.path.join(self.get_build_directory(), 'test')


class FeatureCppTest(FeatureCategoryCppTest):

  def __init__(self, renv, name):
    super(FeatureCppTest, self).__init__(renv, None, name)

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

    exe = os.path.join(self.get_test_bin_dir(), name, name)
    subprocess.call(exe, stderr=subprocess.STDOUT, shell=True)

  def handle_default(self):
    renv = self.renv

    build_dir = self.get_build_directory()
    test_cfg = renv.get_prop(OPT_CFG)

    # If the build directory is not present we call build.configure first
    if not os.path.exists(build_dir):
      self.get_build_ftr().configure(build_dir, test_cfg)

    map(self.run_test, self.get_test_names())


class FeatureCppTestGTest(FeatureCppTest):

  def __init__(self, renv):
    super(FeatureCppTestGTest, self).__init__(renv, 'gtest')
