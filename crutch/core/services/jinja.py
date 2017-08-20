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

from pkg_resources import Requirement, resource_filename

import jinja2

from crutch.core.features import Feature


RE_VERSION = re.compile(r'\d+\.\d+\.\d+')
RE_DOT_HIDDEN = re.compile(r'.*/\..*$')
RE_JINJA_EXT = re.compile(r'\.(j2|jinja|jinja2)$')
RE_JINJA_FILE = re.compile(r'.*\.(j2|jinja|jinja2)$')


class FeatureJinja(Feature):

  def __init__(self, renv):
    super(FeatureJinja, self).__init__(renv)
    templates = resource_filename(Requirement.parse('crutch'), 'templates')
    self.jenv = jinja2.Environment(loader=jinja2.FileSystemLoader(templates))
    self.current_jinja_globals = list()

#-SUPPORT-----------------------------------------------------------------------

  def mirror_repl_to_jinja_globals(self):
    """
    Call this method before rendering any jenv template to populate the
    current_jinja_globals object with the most recent replacements
    """

    # First, delete already existing current_jinja_globals
    for glob in self.current_jinja_globals:
      del self.current_jinja_globals[glob]

    # Then, populate with fresh ones
    self.renv.repl.fetch()
    self.jenv.globals.update(self.renv.repl)

#-API---------------------------------------------------------------------------

  def copy_folder(self, src_dir, dst_dir, path_repl=None):
    jenv = self.jenv

    self.mirror_repl_to_jinja_globals()

    re_tmpl_prefix = re.compile(r'^' + src_dir)
    templates = filter(re_tmpl_prefix.match, jenv.list_templates())

    for tmpl_src in templates:
      filename = re_tmpl_prefix.sub('', tmpl_src)

      # Apply path substitutions if any
      if path_repl:
        for repl in path_repl.keys():
          regex = re.compile(repl)
          filename = regex.sub(path_repl[repl], filename)

      filename = dst_dir + filename

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
