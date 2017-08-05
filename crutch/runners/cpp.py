import subprocess
import sys
import os

from runner import Runner


class CPPRunner(Runner):

  def __init__(self, opts, env, repl, cfg):
    super(CPPRunner, self).__init__(opts, env, repl, cfg)
    self.generators = {'xcode': 'Xcode', 'make': 'Unix Makefiles'}

  def get_generator(self):
    return self.generators.get(self.repl['cpp_generator'])

  def parse_config(self):
    if not self.cfg.has_section('cpp'):
      return

    self.repl['cpp_cmake']     = self.cfg.get('cpp', 'cmake')
    self.repl['cpp_generator'] = self.cfg.get('cpp', 'generator')
    self.repl['cpp_build']     = self.cfg.get('cpp', 'build')
    self.repl['cpp_install']   = self.cfg.get('cpp', 'install')
    self.repl['project_config']  = 'Debug'

  def update_config(self):
    pass

  def configure(self):
    repl = self.repl

    command = [repl['cpp_cmake'],
      '-H' + repl['project_folder'],
      '-B' + repl['cpp_build'],
      '-G"' + self.get_generator() + '"',
      '-DCRUTCH_BUILD_TYPE=' + repl['project_config'],
      '-DCMAKE_BUILD_TYPE=' + repl['project_config'],
      '-DCMAKE_INSTALL_PREFIX=' + repl['cpp_install']
    ]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

  def create(self):
    repl = self.repl

    project_folder = repl['project_folder']

    repl['cpp_generator'] = 'xcode'
    repl['cpp_build']   = os.path.join(project_folder, '_build')
    repl['cpp_install'] = os.path.join(project_folder, '_install')
    repl['cpp_cmake']   = 'cmake'
    repl['project_config']  = 'Debug'

    self.init_folder()

  def build(self):
    repl = self.repl

    self.configure()

    command = [repl['cpp_cmake'],
        '--build', repl['cpp_build'],
        '--config', repl['project_config']]

    subprocess.call(' '.join(command), stderr=subprocess.STDOUT, shell=True)

