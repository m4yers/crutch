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
import sys
import os

from crutch.core.features import create_simple_feature_category
from crutch.core.features import Feature, FeatureMenu

NAME = 'file'
OPT_GROUP = 'feature_file_group'
PATH_INCLUDE = 'include'
PATH_SRC = 'src'
EXT_CPP = '.cpp'
EXT_HPP = '.hpp'


class FeatureMenuCppFileManager(FeatureMenu):

  def __init__(self, renv, handler_add=None, handler_remove=None):
    super(FeatureMenuCppFileManager, self).__init__(renv, NAME, 'C++ File Manager')

    add = self.add_action('add', 'Add C++ file group', handler_add)
    add.add_argument(dest=OPT_GROUP, metavar='GROUP', help='C++ file group to add')

    remove = self.add_action('remove', 'Remove C++ file group', handler_remove)
    remove.add_argument(dest=OPT_GROUP, metavar='GROUP', help='C++ file group to remove')


FeatureCategoryCppFile = create_simple_feature_category(FeatureMenuCppFileManager)


class FileGroup(object):

  def __init__(self, name, directory, project):
    self.name = name
    self.directory = directory
    self.project = project
    self.path = name.split('/')
    self.include = [directory, PATH_INCLUDE, project] + self.path
    self.include[-1] = self.include[-1] + EXT_HPP
    self.src = [directory, PATH_SRC, project] + self.path
    self.src[-1] = self.src[-1] + EXT_CPP

  def get_include_path(self):
    return os.path.join(*self.include)

  def get_src_path(self):
    return os.path.join(*self.src)

  def exists(self):
    return os.path.exists(self.get_include_path()) or os.path.exists(self.get_src_path())

  def delete(self):
    if os.path.exists(self.get_include_path()):
      os.remove(self.get_include_path())

    if os.path.exists(self.get_src_path()):
      os.remove(self.get_src_path())

    # Remove empty folders
    path = self.path[:-1]
    while path:
      include = os.path.join(self.directory, PATH_INCLUDE, self.project, *path)
      if not os.listdir(include):
        shutil.rmtree(include)

      src = os.path.join(self.directory, PATH_SRC, self.project, *path)
      if not os.listdir(src):
        shutil.rmtree(src)

      path = path[:-1]

  def __repr__(self):
    return '[FileGroup {}]'.format(self.name)

  def __str__(self):
    return self.__repr__()

  def __hash__(self):
    return hash(self.name)

  def __eq__(self, other):
    return self.name == other.name

  def __ne__(self, other):
    return not self.__eq__(other)


class FeatureCppFileManager(Feature):

  def __init__(self, renv):
    self.jinja_ftr = renv.feature_ctrl.get_active_feature('jinja')
    super(FeatureCppFileManager, self).__init__(renv)

  def register_menu(self):
    return FeatureMenuCppFileManager(
        self.renv,
        handler_add=self.action_add,
        handler_remove=self.action_remove)

#-API---------------------------------------------------------------------------

  def action_add(self):
    renv = self.renv

    project_name = renv.get_project_name()
    project_directory = renv.get_project_directory()

    group = FileGroup(renv.get_prop(OPT_GROUP), project_directory, project_name)

    if group.exists():
      print "File group '{}' already exists".format(group.name)
      sys.exit(1)

    jdir = os.path.join(renv.get_project_type(), 'other', NAME)
    psub = {'FileGroupRepl': os.path.join(project_name, *group.path)}

    renv.set_prop(OPT_GROUP, group.name, mirror_to_repl=True)

    self.jinja_ftr.copy_folder(jdir, project_directory, psub)

  def action_remove(self):
    renv = self.renv

    project_name = renv.get_project_name()
    project_directory = renv.get_project_directory()

    group = FileGroup(renv.get_prop(OPT_GROUP), project_directory, project_name)

    if not group.exists():
      print "File group '{}' does not exist".format(group.name)
      sys.exit(1)

    group.delete()
