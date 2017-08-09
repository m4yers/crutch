import unittest

from crutch.core.menu import create_crutch_menu


class MenuTest(unittest.TestCase):

  def test_feature(self):
    menu = create_crutch_menu()
    opts = menu.parse(['new', 'cpp', '-f', 'xcode'])
    expected = {'feature': 'new', 'project_type': 'cpp', 'project_features': ['xcode']}
    self.assertDictContainsSubset(expected, vars(opts))

  def test_feature_action(self):
    menu = create_crutch_menu()


    build = menu.add_feature('build', 'Build project')
    build.add_argument(
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
    expected = {'feature': 'build', 'feature_build_config': None, 'project_directory': '.'}
    self.assertDictContainsSubset(expected, vars(opts))

    opts = menu.parse(['test', 'add', 'core/test'])
    expected = {'feature': 'test', 'action': 'add', 'feature_test_add_group': 'core/test'}
    self.assertDictContainsSubset(expected, vars(opts))

    opts = menu.parse(['file', 'add', 'core/feature'])
    expected = {'feature': 'file', 'action': 'add', 'feature_file_add_group': 'core/feature'}
    self.assertDictContainsSubset(expected, vars(opts))
