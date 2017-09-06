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

from pygments.token import Token


def create_toolbar_handler(is_long_option): #pragma: no cover
  assert callable(is_long_option)

  def get_toolbar_items(_):
    if is_long_option():
      option_mode_token = Token.Toolbar.On
      option_mode = 'Long'
    else:
      option_mode_token = Token.Toolbar.Off
      option_mode = 'Short'

    return [
        (Token.Toolbar, ' [F2] Help '),
        (option_mode_token, ' [F3] Options: {0} '.format(option_mode)),
        (Token.Toolbar, ' [F10] Exit ')
        ]

  return get_toolbar_items
