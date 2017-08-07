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

class Category(object):
  def __init__(self, name, features, default, only_one):
    self.name = name
    self.features = features
    self.default = default
    self.only_one = only_one


class Features(object):

  def __init__(self):
    # category name -> category object map
    self.categories = dict()

    # category name -> selected features list map
    self.parsed = dict()

    # feature name -> category object map
    self.features = dict()

  def __repr__(self):
    enabled = {True: '+', False: '-'}
    default = {True: '!', False: ''}

    features = list()

    for n,c in self.categories.items():
      if n not in self.parsed:
        continue

      features.append('{}: {}'.format(n, ', '.join(
        map(lambda f: '{1}{0}{2}'.format(f,
            enabled.get(f in self.parsed[n]),
            default.get(f in c.default)),
          c.features))))

    return '[{} {}]'.format(self.__class__.__name__, ', '.join(features))

  def add_category(self, name, features, default, only_one):
    if self.categories.has_key(name):
      raise Exception("Category already exists")

    category = Category(name, features, default, only_one)

    self.categories[name] = category
    self.parsed[name] = default

    for f in features:
      self.features[f] = category

  def parse(self, features):
    self.parsed = dict()

    for f in features:
      category = self.features.get(f)
      if not category:
        raise Exception("Cannot find the feature '%s'" % f)

      parsed = self.parsed.get(category.name, [])

      if category.only_one and len(parsed) != 0:
        raise Exception("Feature overlap '%s' with '%s'" % f, parsed)

      parsed.append(f)

      self.parsed[category.name] = parsed

  def get_enabled_features(self, category=None):
    if category:
      return self.parsed.get(category, [])
    return sum(self.parsed.values(), [])

  def get_enabled_categories(self):
    return self.parsed.keys()
