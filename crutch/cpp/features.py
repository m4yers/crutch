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

from core.features import Features

class CPPFeatures(Features):

  def __init__(self):
    super(CPPFeatures, self).__init__()

    self.add_category('cmake_generator', ['xcode', 'make'], ['make'],  only_one=True)
    self.add_category('testing',         ['gtest'],         ['gtest'], only_one=True)


  def get_cmake_generator(self):
    return self.get_enabled_features('cmake_generator')[0]

  def is_xcode(self):
    return self.get_cmake_generator() == 'xcode'

  def is_make(self):
    return self.get_cmake_generator() == 'make'

  def get_test_runner(self):
    return self.get_enabled_features('testing')[0]


  def is_gtest(self):
    return self.get_test_runner() == 'gtest'

  def has_test(self):
    return self.is_gtest()
