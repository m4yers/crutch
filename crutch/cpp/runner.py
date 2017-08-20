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

from crutch.core.runner import Runner

from crutch.core.services import FeatureJinja
from crutch.core.features import FeatureCategory

from crutch.cpp.features.build import FeatureCategoryCppBuild
from crutch.cpp.features.build import FeatureCppBuildMake, FeatureCppBuildXcode

from crutch.cpp.features.file import FeatureCategoryCppFile
from crutch.cpp.features.file import FeatureCppFileManager

from crutch.cpp.features.test import FeatureCategoryCppTest
from crutch.cpp.features.test import FeatureCppTestGTest

class RunnerCpp(Runner):

  def __init__(self, renv):
    super(RunnerCpp, self).__init__(renv)

    self.register_feature_category_class(
        'services',
        FeatureCategory,
        features=['jinja'])
    self.register_feature_class('jinja', FeatureJinja)

    self.register_feature_category_class(
        'build',
        FeatureCategoryCppBuild,
        features=['make', 'xcode'],
        defaults=['make'])
    self.register_feature_class('make', FeatureCppBuildMake)
    self.register_feature_class('xcode', FeatureCppBuildXcode)

    self.register_feature_category_class(
        'file',
        FeatureCategoryCppFile,
        features=['file_manager'],
        defaults=['file_manager'],
        requires=['jinja'])
    self.register_feature_class('file_manager', FeatureCppFileManager)

    self.register_feature_category_class(
        'test',
        FeatureCategoryCppTest,
        features=['gtest'],
        defaults=['gtest'],
        requires=['build', 'jinja'])
    self.register_feature_class('gtest', FeatureCppTestGTest)

    self.register_default_run_feature('build')
