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

import codecs
import shutil
import re
import os

RE_VERSION = re.compile(r'\d+\.\d+\.\d+')
RE_DOT_HIDDEN = re.compile(r'.*/\..*$')
RE_PROJECT_NAME = re.compile(r'project|ProjectName')
RE_JINJA_EXT = re.compile(r'\.(j2|jinja|jinja2)$')
RE_JINJA_FILE = re.compile(r'.*\.(j2|jinja|jinja2)$')

from crutch.core.features import Feature, FeatureCategory
from crutch.core.runner import Runner


class FeatureNew(Feature):

  def register_properties(self):
    renv = self.renv

    project_directory = os.path.abspath(renv.get_prop('project_directory'))

    renv.set_prop('user_name', renv.get_prop('os_login'), True, True)
    renv.set_prop('project_directory', project_directory, mirror_to_repl=True)
    renv.set_prop(
        'project_name',
        renv.get_prop('project_name') or os.path.basename(project_directory), True, True)
    # Remove ourselves from the list
    renv.set_prop(
        'project_features',
        renv.get_prop('project_features')[1:] or 'default', mirror_to_config=True)

  def handle(self):
    renv = self.renv

    project_type = renv.get_prop('project_type')
    project_name = renv.get_prop('project_name')
    project_directory = renv.get_prop('project_directory')

    folders = ['main'] + ['features' + os.path.sep + f for f in renv.get_project_features()]

    jenv = renv.jenv

    renv.mirror_repl_to_jinja_globals()

    for folder in folders:
      re_tmpl_prefix = re.compile(r'^' + project_type + os.path.sep + folder)
      templates = filter(re_tmpl_prefix.match, jenv.list_templates())

      for tmpl_src in templates:
        filename = re_tmpl_prefix.sub('', tmpl_src)
        filename = RE_PROJECT_NAME.sub(project_name, filename)
        filename = project_directory + filename

        # Do not override existing files
        if os.path.exists(filename):
          continue

        # Create the containing folder if does not exist already
        folder = os.path.dirname(filename)
        if not os.path.exists(folder):
          os.makedirs(folder)

        tmpl = jenv.get_template(tmpl_src)

        # If the file is not a template just copy it
        if not RE_JINJA_FILE.match(filename):
          shutil.copyfile(tmpl.filename, filename)
          continue

        # Drop .jenv extension
        filename = RE_JINJA_EXT.sub('', filename)

        with codecs.open(filename, 'w', 'utf-8') as out:
          out.write(tmpl.render())


class RunnerNew(Runner):

  def __init__(self, renv):
    super(RunnerNew, self).__init__(renv)
    self.register_feature_category_class(
        'crutch',
        FeatureCategory,
        features=['new'],
        defaults=['new'])
    self.register_feature_class('new', FeatureNew)
