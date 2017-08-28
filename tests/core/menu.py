import unittest

from crutch.core.runtime import RuntimeEnvironment
from crutch.core.menu import create_crutch_menu


class MenuTest(unittest.TestCase):

  def setUp(self):
    self.renv = RuntimeEnvironment(None)
    self.renv.menu = create_crutch_menu(self.renv)

  def test_feature_action(self):
    menu = self.renv.menu

    build = menu.add_feature('build', 'Build project')
    actions = build.add_actions()
    default = actions.add_action('default')
    default.add_argument(
        '-c', '--config', dest='config', metavar='CONFIG',
        help='Build configuration')

    files = menu.add_feature('file', 'File manager')
    actions = files.add_actions()
    add = actions.add_action('add', 'Add file group')
    add.add_argument(dest='group', metavar='GROUP', help='Group name')
    remove = actions.add_action('remove', 'Remove file group')
    remove.add_argument(dest='group', metavar='GROUP', help='Group name')

    test = menu.add_feature('test', 'Test project')
    actions = test.add_actions()
    add = actions.add_action('add', 'Add test group')
    add.add_argument(dest='group', metavar='GROUP', help='Group name')
    remove = actions.add_action('remove', 'Remove test group')
    remove.add_argument(dest='group', metavar='GROUP', help='Group name')


    opts = menu.parse(['build'])
    expected = {'run_feature': 'build', 'action': 'default',\
                'config': None, 'prompt': None}
    self.assertDictContainsSubset(expected, opts)

    opts = menu.parse(['test', 'add', 'core/test'])
    expected = {'run_feature': 'test', 'action': 'add', 'group': 'core/test'}
    self.assertDictContainsSubset(expected, opts)

    opts = menu.parse(['file', 'add', 'core/feature'])
    expected = {'run_feature': 'file', 'action': 'add', 'group': 'core/feature'}
    self.assertDictContainsSubset(expected, opts)
