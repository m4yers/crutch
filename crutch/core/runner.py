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
import re
import os

RE_VERSION = re.compile("\d+\.\d+\.\d+")
RE_DOT_HIDDEN = re.compile(r'.*/\..*$')
RE_PROJECT_NAME = re.compile(r'project|ProjectName')
RE_JINJA_EXT = re.compile(r'\.(j2|jinja|jinja2)$')


class Runner(object):

  def __init__(self, opts, env, repl, cfg):
    self.opts = opts
    self.env = env
    self.repl = repl
    self.cfg = cfg

    self.dispatchers = {
        'new':   self.create,
        'build': self.build,
        'clean': self.clean,
        'info':  self.info
    }

  def init_folder(self):
    repl = self.repl
    env = self.env

    project_type   = repl['project_type']
    project_name   = repl['project_name']
    project_folder = repl['project_folder']

    # TODO uncomment
    # if os.path.exists(project_folder):
    # print 'The "{}" project already exists. Exit.'.format(project_name)
    # exit

    re_project_type = re.compile(r'^' + project_type)
    templates = filter(re_project_type.match, env.list_templates())

    # TODO do not copy unneeded files
    # TODO do not modify non-jinja files
    for tmpl_src in templates:
      tmpl = env.get_template(tmpl_src)

      filename = re_project_type.sub('', tmpl_src)
      filename = RE_PROJECT_NAME.sub(project_name, filename)
      filename = RE_JINJA_EXT.sub('', filename)
      filename = project_folder + filename

      folder = os.path.dirname(filename)
      if not os.path.exists(folder):
        os.makedirs(folder)

      with codecs.open(filename, 'w', 'utf-8') as f:
        f.write(tmpl.render())

  def parse_config(self):
    pass

  def update_config(self):
    pass

  def create(self):
    print '[NOT IMPLEMENTED] Runner.create'
    pass

  def build(self):
    print '[NOT IMPLEMENTED] Runner.build'
    pass

  def clean(self):
    print '[NOT IMPLEMENTED] Runner.clean'
    pass

  def info(self):
    print '[NOT IMPLEMENTED] Runner.info'
    pass

  def run(self):
    action = self.opts.get('action')
    self.parse_config()
    self.dispatchers.get(action)()
    pass
