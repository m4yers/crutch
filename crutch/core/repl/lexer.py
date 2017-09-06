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

from pygments.lexer import RegexLexer
from pygments.lexer import words
from pygments.token import Keyword, Text, Name

from crutch.core.runtime import RuntimeEnvironment

def get_menu():
  return RuntimeEnvironment.get_default().menu

def create_actions_list():
  menu = RuntimeEnvironment.get_default().menu

  features = menu.features.keys()
  actions = list()
  options = list()
  names = list()

  for ftr_menu in menu.features.values():
    for argument in [a for a in ftr_menu.arguments if a.is_optional()]:
      options.append(argument.short_name)
      options.append(argument.long_name)

    if not ftr_menu.actions:
      continue

    actions.extend(ftr_menu.actions.actions.keys())

    for ftr_action in ftr_menu.actions.actions.values():
      for argument in ftr_action.arguments:
        if argument.is_optional():
          options.append(argument.short_name)
          options.append(argument.long_name)

        if argument.choices:
          names.extend(argument.choices)

  return tuple(set(features)), tuple(set(actions)), tuple(set(options)), tuple(set(names))

def create_lexer(): #pragma: no cover
  class CommandLexer(RegexLexer):
    name = 'Command Line'
    aliases = ['cli']
    filenames = []

    crutch_features, crutch_actions, crutch_options, crutch_names = create_actions_list()

    tokens = {
        'root': [
            (words(crutch_features, prefix=r'^', suffix=r'\b'), Keyword.Namespace),
            (words(crutch_actions, prefix=r'', suffix=r'\b'), Keyword.Namespace),
            (words(crutch_options, prefix=r'', suffix=r'\b'), Keyword.Type),
            (words(crutch_names, prefix=r'', suffix=r'\b'), Name),
            (r'.*\n', Text)]
        }
  return CommandLexer
