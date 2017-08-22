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

from __future__ import unicode_literals

import shlex

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.contrib.completers import WordCompleter
from pygments.style import Style
from pygments.token import Token
from pygments.styles.default import DefaultStyle

class DocumentStyle(Style):
  styles = {
      Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
      Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
      Token.Menu.Completions.ProgressButton: 'bg:#003333',
      Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
  }
  styles.update(DefaultStyle.styles)

class Prompt(object):

  def __init__(self, renv):
    self.renv = renv

  def activate(self):
    completer = WordCompleter(['build', 'test', 'feature', 'new'])
    history = InMemoryHistory()
    line = prompt('> ', completer=completer, style=DocumentStyle, history=history)
    return shlex.split(line)
