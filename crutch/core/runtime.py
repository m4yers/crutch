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

from crutch.core.properties import Properties
from crutch.core.replacements import Replacements
from crutch.core.features import FeatureCtrl


class RuntimeEnvironment(object):
  """
  Object of this class holds all necessary utility to get runner run
  """

  def __init__(self, menu, runners):
    self.menu = menu
    self.runners = runners
    self.props = Properties()
    self.repl = Replacements()
    self.prop_to_repl_mirror = self.repl.add_provider('prop_to_repl_mirror', dict())
    self.feature_ctrl = FeatureCtrl(self)

  def update_properties(self, props):
    self.props.update(props)

  def update_cli_properties(self, props):
    self.props.update_cli(props)

  def update_config_filename(self, config):
    self.props.update_config(config)

  def get_stage_properties(self):
    return self.props.stage

  def get_default_properties(self):
    return self.props.defaults

  def get_run_feature(self):
    return self.get_prop('run_feature')

  def get_project_features(self):
    return self.get_prop('project_features')

  def get_crutch_directory(self):
    return self.get_prop('crutch_directory')

  def get_project_directory(self):
    return self.get_prop('project_directory')

  def get_project_name(self):
    return self.get_prop('project_name')

  def get_project_type(self):
    return self.get_prop('project_type')

  def get_prop(self, name, default=None):
    return self.props.get(name, default)

  def set_prop(self, name, value, mirror_to_config=False, mirror_to_repl=False):
    self.props[name] = value
    if mirror_to_config:
      self.mirror_props_to_config([name])
    if mirror_to_repl:
      self.mirror_props_to_repl([name])

  def set_prop_if_not_in(self, name, value, mirror_to_config=False, mirror_to_repl=False):
    if name not in self.props:
      self.set_prop(name, value, mirror_to_config, mirror_to_repl)

  def config_load(self):
    self.props.config_load()

  def config_flush(self):
    self.props.config_flush()

  def mirror_props_to_config(self, properties):
    for prop in properties:
      self.props.config_update(prop, self.props[prop])

  def mirror_props_to_repl(self, properties):
    """
    Copies every property in properties list from Properties container into
    Replacements containers. This method does not perform cleanup, and won't
    delete previously mirrored properties
    """

    for prop in properties:
      self.prop_to_repl_mirror[prop] = self.props[prop]


