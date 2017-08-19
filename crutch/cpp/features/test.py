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
import shutil
import sys
import re
import os

from crutch.core.features import create_simple_feature_category
from crutch.core.features import Feature, FeatureMenu

import crutch.cpp.features.build as Build

NAME = 'test'
OPT_CFG = 'feature_test_config'
OPT_GROUP = 'feature_test_group'
OPT_TESTS = 'feature_test_tests'


RE_TEST_ALLOWED_NAME = re.compile(r'[a-zA-Z_]+')

class FeatureMenuCppTest(FeatureMenu):

  def __init__(self, renv, name=NAME,\
      handler_default=None, handler_add=None, handler_remove=None):
    super(FeatureMenuCppTest, self).__init__(renv, name, 'Test C++ Project')
    default = self.add_default_action('Test project', handler_default)
    default.add_argument(
        '-c', '--config', dest=OPT_CFG, metavar='CONFIG',
        default='debug', choices=['debug', 'release'],
        help='Select project config')
    default.add_argument(
        '-t', '--tests', dest=OPT_TESTS, metavar='TESTS',
        default=None, nargs='*', help='Select tests to run')

    add = self.add_action('add', 'Add test file group', handler_add)
    add.add_argument(dest=OPT_GROUP, metavar='GROUP', help='Group name')

    remove = self.add_action('remove', 'Remove test file group', handler_remove)
    remove.add_argument(dest=OPT_GROUP, metavar='GROUP', help='Group name')


FeatureCategoryCppTest = create_simple_feature_category(FeatureMenuCppTest)


class FeatureCppTest(Feature):

  def __init__(self, renv, name):
    self.name = name
    self.build_ftr = renv.feature_ctrl.get_singular_active_feature(Build.NAME)
    self.jinja_ftr = renv.feature_ctrl.get_active_feature('jinja')
    super(FeatureCppTest, self).__init__(renv)

  def register_menu(self):
    return FeatureMenuCppTest(
        self.renv,
        self.name,
        handler_default=self.action_default,
        handler_add=self.action_add,
        handler_remove=self.action_remove)

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
    tests = self.get_test_names()
    tests = set(tests) & set(renv.get_prop(OPT_TESTS) or tests)

    # Always reconfigure the build folder since there might be new tests
    self.build_ftr.configure(build_dir, test_cfg)

    map(self.run_test, tests)

  def action_add(self):
    renv = self.renv

    project_type = renv.get_project_type()

    group = renv.get_prop(OPT_GROUP)

    if not RE_TEST_ALLOWED_NAME.match(group):
      print "'{}' is not a valid test name".format(group)
      sys.exit(1)

    if group in self.get_test_names():
      print "'{}' already exists".format(group)
      sys.exit(1)

    renv.mirror_props_to_repl([OPT_GROUP, 'project_name'])

    self.jinja_ftr.copy_folder(
        os.path.join(project_type, 'other', self.name, 'test'),
        os.path.join(self.get_test_src_dir(), group))

  def action_remove(self):
    renv = self.renv

    group = renv.get_prop(OPT_GROUP)

    if not group in self.get_test_names():
      print "'{}' does not exist".format(group)
      sys.exit(1)

    shutil.rmtree(os.path.join(self.get_test_src_dir(), group))


class FeatureCppTestGTest(FeatureCppTest):

  def __init__(self, renv):
    super(FeatureCppTestGTest, self).__init__(renv, 'gtest')
