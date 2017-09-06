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

import logging

import crutch.core.lifecycle as Lifecycle


class Logging(object):

  def __init__(self, renv):
    self.renv = renv
    self.logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    self.logger.addHandler(handler)
    self.logger.setLevel(logging.WARNING)

    self.table = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
        }

    self.renv.lifecycle.add_hook_before(
        Lifecycle.CONFIG_FLUSH, self.update_config)
    self.renv.lifecycle.add_hook_after(
        Lifecycle.CONFIG_LOAD, self.update_level)

  def update_config(self):
    self.renv.set_prop(
        'crutch_logging_level',
        logging.getLevelName(self.logger.getEffectiveLevel()).lower(),
        mirror_to_config=True)

  def update_level(self):
    level = self.renv.props.config.get('crutch_logging_level', None)
    if not level:
      return

    lowered = level.lower()
    if lowered not in self.table:
      self.logger.error("Unknown logging error %s", level)
      return

    self.logger.setLevel(self.table[lowered])

