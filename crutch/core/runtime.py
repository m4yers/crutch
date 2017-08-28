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

from crutch.core.properties import Properties
from crutch.core.replacements import Replacements, GenerativeReplacementsProvider
from crutch.core.features.ctrl import FeatureCtrl

from crutch.core.exceptions import StopException

import crutch.core.lifecycle as Lifecycle


class RuntimeEnvReplProvider(GenerativeReplacementsProvider):

  def __init__(self, renv):
    self.renv = renv
    GenerativeReplacementsProvider.__init__(self)

  def generate(self):
    self.data = dict()
    self.data['project_username'] = self.renv.get_prop('project_username')
    self.data['project_name'] = self.renv.get_project_name()
    self.data['project_type'] = self.renv.get_project_type()
    self.data['project_directory'] = self.renv.get_project_directory()
    self.data['crutch_python'] = self.renv.get_prop('crutch_python')
    self.data['crutch_version'] = self.renv.get_prop('crutch_version')
    self.data['sys_login'] = self.renv.get_prop('sys_login')
    return self.data

class RuntimeEnvironment(object):
  """
  Object of this class holds all necessary utility to get runner run
  """

  Default = None

  def __init__(self, runners):
    self.menu = None
    self.prompt = None
    self.runners = runners
    self.props = Properties()
    self.repl = Replacements()
    self.feature_ctrl = FeatureCtrl(self)
    self.lifecycle = Lifecycle.Lifecycle()
    self.prop_to_repl_mirror = self.repl.add_provider('prop-to-repl-mirror', dict())
    self.repl.add_provider('runtime-env-repl', RuntimeEnvReplProvider(self))

  @staticmethod
  def get_default():
    assert RuntimeEnvironment.Default
    return RuntimeEnvironment.Default

  def set_as_default(self):
    assert RuntimeEnvironment.Default is None
    RuntimeEnvironment.Default = self

  def create_runner(self, name):
    return self.runners.get(name)(self)

  def update_properties(self, props):
    self.props.update(props)

  def update_cli_properties(self, props):
    self.props.update_cli(props)

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

  def get_crutch_config(self):
    return self.get_prop('crutch_config')

  def get_project_directory(self):
    return self.get_prop('project_directory')

  def get_project_name(self):
    return self.get_prop('project_name')

  def get_project_type(self):
    return self.get_prop('project_type')

  def del_prop(self, name):
    del self.props[name]

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
    self.lifecycle.mark(Lifecycle.CONFIG_LOAD, Lifecycle.ORDER_BEFORE)
    crutch_config = self.get_crutch_config()
    if not crutch_config:
      raise StopException(StopException.ECFG, 'Crutch config is not set')
    self.props.update_config(crutch_config)
    self.props.config_load()
    self.lifecycle.mark(Lifecycle.CONFIG_LOAD, Lifecycle.ORDER_AFTER)

  def config_flush(self):
    self.lifecycle.mark(Lifecycle.CONFIG_FLUSH, Lifecycle.ORDER_BEFORE)
    crutch_config = self.get_crutch_config()
    if not crutch_config:
      raise StopException(StopException.ECFG, 'Crutch config is not set')
    self.props.update_config(crutch_config)
    self.props.config_flush()
    self.lifecycle.mark(Lifecycle.CONFIG_FLUSH, Lifecycle.ORDER_AFTER)

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
