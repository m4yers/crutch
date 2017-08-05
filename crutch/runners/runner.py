import codecs
import re
import os

RE_VERSION = re.compile("\d+\.\d+\.\d+")
RE_DOT_HIDDEN = re.compile(r'.*/\..*$')
RE_PROJECT_NAME = re.compile(r'project|ProjectName')
RE_JINJA_EXT = re.compile(r'\.(j2|jinja|jinja2)$')


class Runner(object):

  def __init__(self, opts, env, repl, cfg):
    self.opts = opts
    self.env = env
    self.repl = repl
    self.cfg = cfg

    self.dispatchers = {
        'new':   self.create,
        'build': self.build,
        'clean': self.clean,
        'info':  self.info
    }

  def init_folder(self):
    repl = self.repl
    env = self.env

    project_type   = repl['project_type']
    project_name   = repl['project_name']
    project_folder = repl['project_folder']

    # TODO uncomment
    # if os.path.exists(project_folder):
    # print 'The "{}" project already exists. Exit.'.format(project_name)
    # exit

    re_project_type = re.compile(r'^' + project_type)
    templates = filter(re_project_type.match, env.list_templates())

    # TODO do not copy unneeded files
    # TODO do not modify non-jinja files
    for tmpl_src in templates:
      tmpl = env.get_template(tmpl_src)

      filename = re_project_type.sub('', tmpl_src)
      filename = RE_PROJECT_NAME.sub(project_name, filename)
      filename = RE_JINJA_EXT.sub('', filename)
      filename = project_folder + filename

      folder = os.path.dirname(filename)
      if not os.path.exists(folder):
        os.makedirs(folder)

      with codecs.open(filename, 'w', 'utf-8') as f:
        f.write(tmpl.render())

  def parse_config(self):
    pass

  def update_config(self):
    pass

  def create(self):
    print '[NOT IMPLEMENTED] Runner.create'
    pass

  def build(self):
    print '[NOT IMPLEMENTED] Runner.build'
    pass

  def clean(self):
    print '[NOT IMPLEMENTED] Runner.clean'
    pass

  def info(self):
    print '[NOT IMPLEMENTED] Runner.info'
    pass

  def run(self):
    action = self.opts.get('action')
    self.parse_config()
    self.dispatchers.get(action)()
    pass
