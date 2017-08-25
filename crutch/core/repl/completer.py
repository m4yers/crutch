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

import shlex

from prompt_toolkit.completion import Completer, Completion


class ArgumentsSequence(object):

  def __init__(self, words):
    self.sequence = words

  def empty(self):
    return len(self.sequence) == 0

  def top(self):
    assert not self.empty()
    return self.sequence[-1]

  def top_is_opt(self):
    return self.top()[0] == '-'

  def top_is_opt_short(self):
    return self.top()[0] == '-' and self.top()[1] != '-'

  def top_is_opt_long(self):
    return self.top()[0:2] == '--'

  def pop(self):
    assert not self.empty()
    return self.sequence.pop()


class CrutchCompleter(Completer):

  def __init__(self, renv):
    super(CrutchCompleter, self).__init__()
    self.renv = renv
    self.menu = renv.menu

  def get_feature_completions(self, partial):
    result = []
    features = self.menu.features.keys()

    if partial:
      for name in features:
        if name.find(partial) == 0:
          result.append(Completion(name, -len(partial)))
    else:
      for name in features:
        result.append(Completion(name))

    return result

  def get_actions_completions(self, words, partial):
    result = []
    feature = words[0]
    menu = self.menu.features.get(feature, None)

    if not menu:
      return result

    for action in menu.actions.actions.keys():
      if partial and action.find(partial) != 0:
        continue

      if action == 'default':
        continue

      result.append(Completion(
          text=action,
          start_position=-len(partial) if partial else 0))

    # since we omit default action we need to add options as well
    if not partial:
      result.extend(self.get_arguments_completions(words + ['default'], partial))

    return result

  def get_nargs_q_completions(self, optional, sequence, partial):
    result = []
    need_more = True
    choices = optional.choices or []
    if choices:

      # If the next word is once of the choices we drop it and continue
      if not sequence.empty() and sequence.top() in choices:
        sequence.pop()
        need_more = False

      # If partial matches one of the choices we yield the completion and return for now
      elif partial:
        maybe = [c for c in choices if c.find(partial) == 0]
        if maybe:
          for choice in maybe:
            result.append(Completion(text=choice, start_position=-len(partial)))

      # Otherwise we just list the choices if any
      else:
        for choice in choices:
          result.append(Completion(text=choice, start_position=0))

    else:
      if not sequence.empty() and not sequence.top_is_opt():
        sequence.pop()
        need_more = False

    return result, need_more

  def get_nargs_s_completions(self, optional, sequence, partial):
    result = []
    need_more = True
    choices = optional.choices or []
    if choices:
      while not sequence.empty() and not sequence.top_is_opt():
        value = sequence.pop()
        choices.remove(value)

      if sequence.empty():
        if partial:
          for choice in [c for c in choices if c.find(partial) == 0]:
            result.append(Completion(text=choice, start_position=-len(partial)))
        else:
          for choice in choices:
            result.append(Completion(text=choice, start_position=0))
    else:
      while not sequence.empty() and not sequence.top_is_opt():
        sequence.pop()
        need_more = False

    return result, need_more

  def optionals_to_completions(self, optionals, partial):
    result = []
    if partial:
      for optional in optionals.values():
        if optional.short_name.find(partial) != 0 or optional.long_name.find(partial) != 0:
          continue
        result.append(Completion(
            text=optional.long_name,
            display='/'.join([optional.short_name, optional.long_name]),
            start_position=-len(partial)))
    else:
      for optional in optionals.values():
        result.append(Completion(
            text=optional.long_name,
            display='/'.join([optional.short_name, optional.long_name])))

    return result

  def positionals_to_completions(self, positionals, partial):
    result = []

    if partial:
      for positional in positionals:
        for choice in [c for c in (positional.choices or []) if c.find(partial) == 0]:
          result.append(Completion(choice, start_position=-len(partial)))
    else:
      for positional in positionals:
        for choice in (positional.choices or []):
          result.append(Completion(choice))

    return result

  def get_arguments_completions(self, words, partial):
    result = []
    sequence = ArgumentsSequence(list(reversed(words)))
    feature = sequence.pop()
    menu = self.menu.features.get(feature, None)

    if not menu:
      return result

    actions = menu.actions.actions

    action = sequence.top()
    if action in actions.keys():
      sequence.pop()
    elif 'default' in actions.keys():
      action = 'default'
    else:
      return result

    arguments = actions.get(action).arguments
    positionals = [a for a in arguments if a.is_positional()]
    optionals = {a.short_name:a for a in arguments if a.is_optional()}
    long_to_short = {a.long_name:a.short_name for a in arguments if a.is_optional()}

    # Before we provide completions we need to remove already used options
    while not sequence.empty():
      if sequence.top_is_opt():
        optional = None
        if sequence.top_is_opt_short():
          optional = optionals.get(sequence.pop(), None)
        else:
          short = long_to_short.get(sequence.pop(), None)
          if short:
            optional = optionals.get(short, None)

        # Something we do not know about
        if not optional:
          continue

        del optionals[optional.short_name]

        need_more = False
        if optional.nargs == '?':
          completions, need_more = self.get_nargs_q_completions(optional, sequence, partial)
          result.extend(completions)
        elif optional.nargs == '*' or optional.nargs == '+':
          completions, need_more = self.get_nargs_s_completions(optional, sequence, partial)
          result.extend(completions)
        else:
          for _ in range(optional.nargs):
            if sequence.empty() or sequence.top_is_opt():
              need_more = True
              break
            sequence.pop()

        if need_more and sequence.empty():
          return result

      else:
        choice = sequence.pop()
        for positional in positionals:
          choices = positional.choices or []
          if choice in choices and (positional.nargs == '?' or positional.nargs == 1):
            positionals.remove(positional)
            break

    result.extend(self.optionals_to_completions(optionals, partial))
    result.extend(self.positionals_to_completions(positionals, partial))

    return result

  def get_completions(self, document, _):
    partial = document.get_word_before_cursor(WORD=True)
    words = shlex.split(document.text)
    length = len(words)

    if partial:
      words.pop()

    if length == 0 or (length == 1 and partial):
      for completion in self.get_feature_completions(partial):
        yield completion
    elif (length == 1 and not partial) or (length == 2 and partial):
      for completion in self.get_actions_completions(words, partial):
        yield completion
    else:
      for completion in self.get_arguments_completions(words, partial):
        yield completion
