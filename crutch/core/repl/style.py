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

import pygments.styles

from pygments.token import Token
from pygments.util import ClassNotFound
from prompt_toolkit.styles import default_style_extensions, PygmentsStyle


def style_factory(name='default'):
  try:
    style = pygments.styles.get_style_by_name(name)
  except ClassNotFound:
    style = pygments.styles.get_style_by_name('default')

  styles = {}

  styles.update(style.styles)
  styles.update(default_style_extensions)
  styles.update({
      Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
      Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
      Token.Menu.Completions.ProgressButton: 'bg:#003333',
      Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
      Token.Toolbar: 'bg:#222222 #cccccc',
      Token.Toolbar.Off: 'bg:#222222 #004444',
      Token.Toolbar.On: 'bg:#222222 #ffffff',
      Token.Toolbar.Search: 'noinherit bold',
      Token.Toolbar.Search.Text: 'nobold',
      Token.Toolbar.System: 'noinherit bold',
      Token.Toolbar.Arg: 'noinherit bold',
      Token.Toolbar.Arg.Text: 'nobold',
      Token.Pound: 'bg:#a06a2c #222222'
  })

  return PygmentsStyle.from_defaults(style_dict=styles)
