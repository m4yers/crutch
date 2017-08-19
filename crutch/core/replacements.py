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
import os


class GenerativeReplacementsProvider(UserDict.DictMixin):
  """
  This class must be subclassed and method `generate` overridden to fill data
  with new replacements
  """

  def __init__(self, data=None):
    self.data = data or dict()

  def __getitem__(self, key):
    return self.data[key]

  def __setitem__(self, key, value):
    self.data[key] = value

  def __delitem__(self, key):
    del self.data[key]

  def __contains__(self, key):
    return key in self.data[key]

  def keys(self):
    return self.data.keys()

  def generate(self):
    return self.data


class Replacements(UserDict.DictMixin):
  """
  Replacements is a container for replacments providers, it is used to fill in
  the globals dict() of jinja2.Environment. There are two types of providers:

    - static: provides a fixed number of replacements
    - generative: provides replacements generated based on some external
      condition, e.g: feature activation

  Before calling any data on a object of this class you must call fetch()
  first to retrieve all the data from providers
  """

  def __init__(self):
    self.static = dict()
    self.generators = dict()
    self.providers = dict()
    self.data = dict()

  def __getitem__(self, key):
    return self.data[key]

  def __setitem__(self, key, value):
    raise Exception("You cannot set a key from Replacements directly")

  def __delitem__(self, key):
    raise Exception("You cannot delete a key from Replacements directly")

  def __contains__(self, key):
    return key in self.keys()

  def keys(self):
    return self.data.keys()

  def add_provider(self, label, provider=None):
    provider = provider if provider is not None else dict()
    self.providers[label] = provider
    if isinstance(provider, GenerativeReplacementsProvider):
      self.generators[label] = provider
    else:
      self.static[label] = provider
    return provider

  def fetch(self):
    self.data = dict()
    for provider in self.static.values():
      for key in provider:
        if key in self.data:
          raise Exception("Key conflict {}".format(key))
        else:
          self.data[key] = provider[key]

    for provider in self.generators.values():
      provider.generate()
      for key in provider:
        if key in self.data:
          raise Exception("Key conflict {}".format(key))
        else:
          self.data[key] = provider[key]

  def get_print_info(self):
    self.fetch()

    def offset(lines, spaces=0):
      return ''.join((os.linesep for _ in range(lines))) + ''.join((' ' for _ in range(spaces)))

    def format_dict(dic):
      return offset(1, 2).join(
          ['{}: {}'.format(key, value) for key, value in sorted(dic.items())])

    result = 'REPLACEMENTS' + offset(2)

    result += 'Statics:' + offset(1, 1)
    for label, provider in sorted(self.static.iteritems()):
      result += offset(1, 1) + label + ':'
      result += offset(1, 2) + format_dict(provider)
      result += offset(2)

    result += 'Generators:' + offset(1, 1)
    for label, provider in sorted(self.generators.iteritems()):
      result += offset(1, 1) + label + ':'
      result += offset(1, 2) + format_dict(provider)
      result += offset(2)

    return result
