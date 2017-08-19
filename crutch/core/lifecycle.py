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


# Lifecycle:
# - CRUTCH_START
#     - FEATURE_ACTIVATION
#       - BUILD_DEPENDENCY_GRAPH
#       - (for every category)
#         - CATEGORY_CREATE
#         - FEATURE_CREATE
#   - CMD_PARSE
#   - RUNNER_RUN
#     - FEATURE_DEACTIVATION
#       - (for every category)
#         - FEATURE_DESTROY
#         - CATEGORY_DESTROY
#   - CONFIG_FLUSH
# - CRUTCH_STOP

CRUTCH_START = 'crutch-start'
CONFIG_LOAD = 'config-load'
FEATURE_ACTIVATION = 'feature-activation'
BUILD_DEPENDENCY_GRAPH = 'build-dependency-graph'
CATEGORY_CREATE = 'category-create'
FEATURE_CREATE = 'feature-create'
CMD_PARSE = 'cmd-parse'
RUNNER_RUN = 'runner-run'
FEATURE_DEACTIVATION = 'feature-deactivation'
FEATURE_DESTROY = 'feature-destroy'
CATEGORY_DESTROY = 'category-destroy'
CONFIG_FLUSH = 'config-flush'
CRUTCH_STOP = 'crutch-stop'

ORDER_NONE = 'order-none'
ORDER_BEFORE = 'order-before'
ORDER_AFTER = 'order-after'

class Lifecycle(object):

  def __init__(self):
    self.hooks = dict()
    self.tracing = False

  def enable_tracing(self):
    self.tracing = True

  def disable_tracing(self):
    self.tracing = False

  def add_hook(self, phase, order, hook=ORDER_NONE):
    orders = self.hooks.get(phase, dict())
    hooks = orders.get(order, list())
    hooks.append(hook)
    orders[order] = hooks
    self.hooks[phase] = orders

  def add_hook_before(self, phase, hook):
    self.add_hook(phase, ORDER_BEFORE, hook)

  def add_hook_after(self, phase, hook):
    self.add_hook(phase, ORDER_AFTER, hook)

  def mark(self, phase, order=ORDER_NONE, info=''):
    if self.tracing:
      print 'LIFECYCLE: {} {} {}'.format(order, phase, info)

    if phase not in self.hooks:
      return

    orders = self.hooks[phase]

    if order not in orders:
      return

    for hook in orders[order]:
      hook(info)
