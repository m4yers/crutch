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
from __future__ import print_function

from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys


def get_key_manager(set_long_options, get_long_options): #pragma: no cover
  assert callable(set_long_options)
  assert callable(get_long_options)

  manager = KeyBindingManager(
      enable_search=True,
      enable_system_bindings=True,
      enable_abort_and_exit_bindings=True)

  @manager.registry.add_binding(Keys.F2)
  def opt_help(event):
    """
    When F2 has been pressed, fill in the "help" command.
    """
    event.cli.current_buffer.insert_text("help")

  @manager.registry.add_binding(Keys.F3)
  def opt_set_options_length(_):
    """
    Enable/Disable long option name suggestion.
    """
    set_long_options(not get_long_options())

  @manager.registry.add_binding(Keys.F10)
  def opt_exit(_):
    """
    When F10 has been pressed, quit.
    """
    # Unused parameters for linter.
    raise EOFError

  @manager.registry.add_binding(Keys.ControlSpace)
  def opt_auto_complete(event):
    """
    Initialize autocompletion at cursor.  If the autocompletion menu is not
    showing, display it with the appropriate completions for the context.  If
    the menu is showing, select the next completion.
    """
    buf = event.cli.current_buffer
    if buf.complete_state:
      buf.complete_next()
    else:
      event.cli.start_completion(select_first=False)

  return manager
