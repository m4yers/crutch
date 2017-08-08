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

import UserDict
import codecs
import json
import os

class FlatJSONConfig(UserDict.DictMixin):

  def __init__(self, filename):
    self.filename = filename
    self.data = dict()

  def get_next_to_last(self, key, create=False):
    path = key.split('_')
    last = path[-1]
    curr = self.data
    for name in path[:-1]:
      if name in curr:
        curr = curr[name]
      else:
        if create:
          curr[name] = dict()
          curr = curr[name]
        else:
          raise KeyError(key)
    return last, curr

  def get_flat_keys(self, current, collection, key=''):
    if not isinstance(current, dict):
      collection.append(key)
      return collection

    for name in current.keys():
      self.get_flat_keys(current[name], collection, '_'.join([key, name]) if key else name)

    return collection

  def remove_empty(self, key):
    path = key.split('_')
    curr = self.data
    for name in path[:-1]:
      if name in curr:
        if not curr[name]:
          del curr[name]
          return
        else:
          curr = curr[name]

  def __getitem__(self, key):
    name, obj = self.get_next_to_last(key)
    return obj[name]

  def __setitem__(self, key, value):
    name, obj = self.get_next_to_last(key, True)
    obj[name] = value

  def __delitem__(self, key):
    name, obj = self.get_next_to_last(key)
    del obj[name]
    self.remove_empty(key)

  def __contains__(self, key):
    return key in self.keys()

  def items(self):
    return [(key, self[key]) for key in self.keys()]

  def keys(self):
    return self.get_flat_keys(self.data, list())

  def load(self):
    with codecs.open(self.filename, 'rU', 'utf-8') as fin:
      self.data = json.load(fin)

  def flush(self):
    with codecs.open(self.filename, 'wU', 'utf-8') as fout:
      json.dump(self.data, fout)


class Properties(UserDict.DictMixin):
  """
  Properties allows to access all properties providers within a single tool
  run and layer them accordingly:

    - stage
    - cli
    - config
    - defaults

  All writes to this object will be done do stage object. Writing to config
  file requires calling explicit methods
  """

  def __init__(self, defaults, config, cli):
    self.defaults = defaults
    self.config = FlatJSONConfig(config) if config else dict()
    self.cli = cli
    self.stage = dict()

    self.providers = [self.stage, self.cli, self.config, self.defaults]

  def __getitem__(self, key):
    for provider in self.providers:
      if key in provider:
        return provider[key]
    return None

  def __setitem__(self, key, value):
    self.stage[key] = value

  def __delitem__(self, key):
    del self.stage[key]

  def __contains__(self, key):
    return key in self.keys()

  def keys(self):
    result = list()
    for provider in self.providers:
      result += provider.keys()
    return list(set(result))

  def config_push(self, selected=None):
    assert isinstance(self.config, FlatJSONConfig)
    properties = selected or self.keys()
    for prop in properties:
      if prop in self.stage:
        self.config[prop] = self.stage[prop]

  def config_update(self, key, value):
    assert isinstance(self.config, FlatJSONConfig)
    self.config[key] = value

  def config_delete(self, key):
    assert isinstance(self.config, FlatJSONConfig)
    del self.config[key]

  def config_load(self):
    assert isinstance(self.config, FlatJSONConfig)
    self.config.load()

  def config_flush(self):
    assert isinstance(self.config, FlatJSONConfig)
    self.config.flush()

  def get_print_info(self):
    offset = os.linesep + ' '
    dline = os.linesep + os.linesep

    def format_dict(dic):
      return offset.join(
          ['{}: {}'.format(key, value) for key, value in sorted(dic.items())])

    result = 'PROPERTIES' + dline

    result += 'Stage:' + offset + format_dict(self.stage) + dline
    result += 'CLI:' + offset + format_dict(self.cli) + dline
    result += 'Config:' + offset + format_dict(self.config) + dline
    result += 'Defaults:' + offset + format_dict(self.defaults) + dline

    return result
