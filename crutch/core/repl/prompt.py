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

from pygments.token import Token

from prompt_toolkit import AbortAction, Application, CommandLineInterface
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import create_prompt_layout, create_eventloop
from prompt_toolkit.filters import Always
from prompt_toolkit.buffer import Buffer, AcceptAction

from crutch.core.repl.lexer import create_lexer
from crutch.core.repl.toolbar import create_toolbar_handler
from crutch.core.repl.keys import get_key_manager
from crutch.core.repl.style import style_factory
from crutch.core.repl.completer import CrutchCompleter

class Prompt(object): #pragma: no cover

  def __init__(self, renv):
    self.renv = renv
    self.is_long = True
    self.cli = None

  def initialize(self):
    history = InMemoryHistory()
    toolbar_handler = create_toolbar_handler(self.get_long_options)

    layout = create_prompt_layout(
        get_prompt_tokens=self.get_prompt_tokens,
        lexer=create_lexer(),
        get_bottom_toolbar_tokens=toolbar_handler)

    buf = Buffer(
        history=history,
        completer=CrutchCompleter(self.renv),
        complete_while_typing=Always(),
        accept_action=AcceptAction.RETURN_DOCUMENT)

    manager = get_key_manager(
        self.set_long_options,
        self.get_long_options)

    application = Application(
        style=style_factory(),
        layout=layout,
        buffer=buf,
        key_bindings_registry=manager.registry,
        on_exit=AbortAction.RAISE_EXCEPTION,
        on_abort=AbortAction.RETRY,
        ignore_case=True)

    eventloop = create_eventloop()

    self.cli = CommandLineInterface(application=application, eventloop=eventloop)

  def get_prompt_tokens(self, _):
    return [(Token.Pound, ' Y '), (Token.Text, ' ')]

  def set_long_options(self, value):
    self.is_long = value

  def get_long_options(self):
    return self.is_long

  def activate(self, reinitialize=False):
    if reinitialize:
      self.initialize()
    assert self.cli
    document = self.cli.run(True)
    return shlex.split(document.text)
