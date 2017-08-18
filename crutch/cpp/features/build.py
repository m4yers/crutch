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


NAME = 'build'
PROP_CMK = 'feature_build_cmake'
OPT_CFG = 'feature_build_config'


class FeatureMenuCppBuild(FeatureMenu):

  def __init__(self, renv, name=NAME, handler_default=None):
    super(FeatureMenuCppBuild, self).__init__(renv, name, 'Build C++ Project')
    default = self.add_default_action('Build project', handler_default)
    default.add_argument(
        '-c', '--config', dest=OPT_CFG, metavar='CONFIG',
        default='debug', choices=['debug', 'release'],
        help='Select project config')


FeatureCategoryCppBuild = create_simple_feature_category(FeatureMenuCppBuild)


class FeatureCppBuild(Feature):

  def __init__(self, renv, name, generator, suffix=''):
    self.name = name
    self.generator = generator
    self.suffix = suffix
    super(FeatureCppBuild, self).__init__(renv)

  def register_menu(self):
    return FeatureMenuCppBuild(self.renv, self.name, self.action_build)

  def register_properties(self):
    super(FeatureCppBuild, self).register_properties()
    self.renv.set_prop_if_not_in(PROP_CMK, 'cmake', mirror_to_config=True)

#-SUPPORT-----------------------------------------------------------------------

  def is_make(self):
    return self.__class__ == FeatureCppBuildMake

  def is_xcode(self):
    return self.__class__ == FeatureCppBuildXcode

  def get_build_directory(self, suffix=None):
    crutch_directory = self.renv.get_crutch_directory()
    return os.path.abspath(os.path.join(crutch_directory, NAME, suffix))

  def configure(self, build_directory, config):
    command = [
        self.renv.get_prop(PROP_CMK),
        '-H' + self.renv.get_prop('project_directory'),
        '-B' + build_directory,
        '-G"' + self.generator + '"',
        '-DCMAKE_BUILD_TYPE=' + config.capitalize()]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

#-ACTIONS-----------------------------------------------------------------------

  def action_build(self):
    build_directory = self.get_build_directory(self.suffix)
    build_config = self.renv.get_prop(OPT_CFG)

    # If not build folder we need to configure cmake first
    if not os.path.exists(build_directory):
      self.configure(build_directory, build_config)

    command = [self.renv.get_prop(PROP_CMK),               \
        '--build', build_directory,                        \
        '--target', 'main',                                \
        '--config', build_config.capitalize()]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)


class FeatureCppBuildMake(FeatureCppBuild):

  def __init__(self, renv):
    super(FeatureCppBuildMake, self).\
        __init__(renv, 'make', 'Unix Makefiles', renv.get_prop(OPT_CFG))


class FeatureCppBuildXcode(FeatureCppBuild):

  def __init__(self, renv):
    super(FeatureCppBuildXcode, self).__init__(renv, 'xcode', 'Xcode')
