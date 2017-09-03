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
import os

import prompter

from crutch.core.exceptions import StopException
from crutch.core.features.basics import create_simple_feature_category
from crutch.core.features.basics import Feature, FeatureMenu

import crutch.cpp.features.build as Build

NAME = 'test'
OPT_CFG = 'feature_test_config'
OPT_TEST = 'feature_test_group'
OPT_TESTS = 'feature_test_tests'
CONFIG_DEBUG = 'debug'
CONFIG_RELEASE = 'release'
CONFIG_CHOICES = [CONFIG_DEBUG, CONFIG_RELEASE]


class FeatureMenuCppTest(FeatureMenu):

  def __init__(self, renv, name=NAME,\
      handler_default=None, handler_add=None, handler_remove=None):
    super(FeatureMenuCppTest, self).__init__(renv, name, 'Test C++ Project')
    default = self.add_default_action('Test project', handler_default)
    default.add_argument(
        '-c', '--config', dest=OPT_CFG, metavar='CONFIG',
        default='debug', choices=CONFIG_CHOICES,
        help='Select project config')
    default.add_argument(
        '-t', '--tests', dest=OPT_TESTS, metavar='TESTS',
        default=[], nargs='*', help='Select tests to run')

    add = self.add_action('add', 'Add test', handler_add)
    add.add_argument(dest=OPT_TEST, metavar='TEST', help='Test name')

    remove = self.add_action('remove', 'Remove test', handler_remove)
    remove.add_argument(dest=OPT_TEST, metavar='TEST', help='Test name')


FeatureCategoryCppTest = create_simple_feature_category(FeatureMenuCppTest)


class Test(object):

  def __init__(self, name):
    self.name = name
    self.path = name.split('/')
    self.target = name.replace('/', '_')

  def __repr__(self):
    return '[Test {}]'.format(self.name)

  def __str__(self):
    return self.__repr__()

  def __hash__(self):
    return hash(self.name)

  def __eq__(self, other):
    return self.name == other.name

  def __ne__(self, other):
    return not self.__eq__(other)


class FeatureCppTest(Feature):

  def __init__(self, renv, name):
    self.name = name
    self.build_ftr = renv.feature_ctrl.get_mono_feature(Build.NAME)
    self.jinja_ftr = renv.feature_ctrl.get_active_feature('jinja')
    super(FeatureCppTest, self).__init__(renv, FeatureMenuCppTest(
        renv,
        name,
        handler_default=self.action_default,
        handler_add=self.action_add,
        handler_remove=self.action_remove))

  def set_up(self):
    psub = {'ProjectNameRepl': self.renv.get_project_name()}
    self.jinja_ftr.copy_folder(
        os.path.join(self.renv.get_project_type(), 'features', self.name),
        self.renv.get_project_directory(),
        psub)

  def tear_down(self):
    shutil.rmtree(self.get_test_src_dir())
    for config in CONFIG_CHOICES:
      bin_dir = self.build_ftr.get_build_directory(config)
      if os.path.exists(bin_dir):
        shutil.rmtree(bin_dir)

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

  def get_tests(self):
    result = list()
    src_dir = self.get_test_src_dir()
    for path, _, _ in os.walk(src_dir):
      if os.path.exists(os.path.join(path, 'CMakeLists.txt')) and \
         os.path.exists(os.path.join(path, 'test.cpp')):
        result.append(Test(path.replace(src_dir + os.path.sep, '')))
    return result

  def run_test(self, test):
    renv = self.renv

    build_dir = self.get_build_directory()
    build_cmk = renv.get_prop(Build.PROP_CMK)
    test_cfg = renv.get_prop(OPT_CFG)

    build = [
        build_cmk,
        '--build', build_dir,
        '--target', test.target,
        '--config', test_cfg]
    subprocess.call(' '.join(build), stderr=subprocess.STDOUT, shell=True)

    suffix = test_cfg.capitalize() if self.build_ftr.is_xcode() else ''
    exe = os.path.join(
        self.get_test_bin_dir(),
        os.path.sep.join(test.path),
        suffix, test.target)
    subprocess.call(exe, stderr=subprocess.STDOUT, shell=True)

#-ACTIONS-----------------------------------------------------------------------

  def action_default(self):
    renv = self.renv

    build_dir = self.get_build_directory()
    test_cfg = renv.get_prop(OPT_CFG)
    tests = self.get_tests()
    tests = set(tests) & set([Test(n) for n \
        in renv.get_prop(OPT_TESTS)] or tests)

    # Always reconfigure the build folder since there might be new tests
    self.build_ftr.configure(build_dir, test_cfg)

    map(self.run_test, tests)

  def action_add(self):
    renv = self.renv

    test = Test(renv.get_prop(OPT_TEST))

    for tst in self.get_tests():
      if test.name == tst.name:
        raise StopException(
            StopException.EFS,
            "'{}' already exists".format(test.name))
      if test.name in tst.name:
        raise StopException(
            StopException.EFS,
            "'{}' is a group of tests".format(test.name))

    renv.set_prop(OPT_TEST, test.target, mirror_to_repl=True)

    jdir = os.path.join(renv.get_project_type(), 'other', self.name)
    jdir_test_group = os.path.join(jdir, 'group')
    jdir_test = os.path.join(jdir, 'test')

    psub = {'ProjectNameRepl': renv.get_project_name()}

    # Init all folders along test path
    fullpath = self.get_test_src_dir()
    path = list(reversed(test.path))
    final = path[0]
    path = path[1:]
    while path:
      fullpath = os.path.join(fullpath, path.pop())
      # If this folder already exists we must change nothing
      if os.path.exists(fullpath):
        continue
      self.jinja_ftr.copy_folder(jdir_test_group, fullpath, psub)

    fullpath = os.path.join(fullpath, final)
    self.jinja_ftr.copy_folder(jdir_test, fullpath, psub)

  def action_remove(self):
    renv = self.renv

    test = Test(renv.get_prop(OPT_TEST))

    if test not in self.get_tests():
      raise StopException(
          StopException.EFS,
          "'{}' does not exist".format(test.name))

    if not prompter.yesno("Do you really want remove this test?"):
      raise StopException("Nothing was removed")

    # Remove test folder
    shutil.rmtree(
        os.path.join(
            self.get_test_src_dir(),
            os.path.sep.join(test.path)))

    # Remove empty folders if any
    path = test.path[:-1]
    while path:
      fullpath = os.path.join(self.get_test_src_dir(), os.path.sep.join(path))
      if len(os.listdir(fullpath)) == 1:
        shutil.rmtree(fullpath)
      path.pop()

    print("Test '{}' was removed".format(test.name))


class FeatureCppTestGTest(FeatureCppTest):

  def __init__(self, renv):
    super(FeatureCppTestGTest, self).__init__(renv, 'gtest')
