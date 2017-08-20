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

import shutil
import os

from crutch.core.features import Feature

class FeatureTemp(Feature):
  """
  FeatureTemp stores links to files and directories to be destroyed upon CRUTCH
  exit
  """

  def __init__(self, renv):
    super(FeatureTemp, self).__init__(renv)
    self.files = list()
    self.directories = list()

#-SUPPORT-----------------------------------------------------------------------

  def clean(self):
    for path in self.files:
      if os.path.exists(path):
        os.remove(path)
    for path in self.directories:
      if os.path.exists(path):
        shutil.rmtree(path)

#-API---------------------------------------------------------------------------

  def add_file(self, path):
    self.files.append(path)

  def add_directory(self, path):
    self.directories.append(path)
