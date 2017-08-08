import unittest
import shutil
import tempfile
import os

THIS_FOLDER = os.path.abspath(os.path.dirname(__file__))
DATA_CONFIG = os.path.join(THIS_FOLDER, 'data', 'config.json')

DATA = {
    'user_name': 'username',
    'project_name': 'blah',
    'project_type': 'test',
    'project_features': ['one', 'two', 'three']
}

from crutch.core.properties import FlatJSONConfig, Properties


class FlatJSONConfigTest(unittest.TestCase):

  def setUp(self):
    self.dir = tempfile.mkdtemp()
    self.filename = os.path.join(self.dir, 'config.json')

    self.config = FlatJSONConfig(self.filename)

  def tearDown(self):
    shutil.rmtree(self.dir)

  def test_config_keys(self):
    self.config.update(DATA)

    self.assertItemsEqual(DATA.keys(), self.config.keys())

    for key in DATA:
      self.assertIn(key, self.config)

    for key in self.config:
      self.assertIn(key, DATA)

  def test_config_load(self):
    shutil.copy(DATA_CONFIG, self.filename)
    self.config.load()

    self.assertDictContainsSubset(DATA, self.config)

  def test_config_flush(self):
    self.config.update(DATA)

    # Make sure in-memory representation match
    self.assertDictContainsSubset(DATA, self.config)

    # Write to disk
    self.config.flush()

    # Verify written DATA
    reader = FlatJSONConfig(self.filename)
    reader.load()

    self.assertDictContainsSubset(DATA, reader)

  def test_config_delete(self):
    shutil.copy(DATA_CONFIG, self.filename)
    self.config.load()

    del self.config['user_name']

    self.assertNotIn('user_name', self.config)
    self.assertIn('project_name', self.config)
    self.assertIn('project_type', self.config)
    self.assertIn('project_features', self.config)

    self.assertEqual(len(self.config.keys()), 3)
    self.assertNotIn('user_name', self.config.keys())
    self.assertIn('project_name', self.config.keys())
    self.assertIn('project_type', self.config.keys())
    self.assertIn('project_features', self.config.keys())


class PropertiesRuntimeDataTest(unittest.TestCase):
  """
  This test verifies that basic read/write of stage properties works.
  No IO involved
  """

  def setUp(self):
    self.defaults = dict()
    self.cli = dict()
    self.props = Properties(self.defaults, '', self.cli)
    self.stage = self.props.stage

  def test_read_write(self):
    self.props['some'] = 'value'

    # Make sure it did't write throught the stage dict()
    self.assertNotIn('some', self.defaults)
    self.assertNotIn('some', self.cli)

    # The values is actually set and can be read
    self.assertDictContainsSubset({'some': 'value'}, self.stage)
    self.assertEqual(self.props['some'], 'value')

  def test_keys(self):
    self.props['one'] = 'one'
    self.props['two'] = 'two'
    self.props['three'] = 'three'

    keys = self.props.keys()

    self.assertEqual(len(keys), 3)
    self.assertIn('one', keys)
    self.assertIn('two', keys)
    self.assertIn('three', keys)


class PropertiesConfigDataTest(unittest.TestCase):

  def setUp(self):
    self.dir = tempfile.mkdtemp()
    self.config = os.path.join(self.dir, 'config.json')

    self.defaults = dict()
    self.cli = dict()
    self.props = Properties(self.defaults, self.config, self.cli)
    self.stage = self.props.stage

  def tearDown(self):
    shutil.rmtree(self.dir)

  def test_config_keys(self):
    self.props.update(DATA)
    self.props.config_push()
    self.assertEqual(DATA.keys(), self.props.keys())

  def test_config_load(self):
    shutil.copy(os.path.join(THIS_FOLDER, 'data', 'config.json'), self.config)
    self.props.config_load()

    self.assertDictContainsSubset(DATA, self.props.config)
    self.assertDictContainsSubset(DATA, self.props)

  def test_config_flush(self):
    for key, value in DATA.items():
      self.props.config_update(key, value)

    # Make sure in-memory representation match
    self.assertDictContainsSubset(DATA, self.props.config)
    self.assertDictContainsSubset(DATA, self.props)

    # Write to disk
    self.props.config_flush()

    # Verify written DATA
    reader = Properties(dict(), self.config, dict())
    reader.config_load()

    self.assertDictContainsSubset(DATA, reader.config)
    self.assertDictContainsSubset(DATA, reader)

  def test_config_delete(self):
    shutil.copy(os.path.join(THIS_FOLDER, 'data', 'config.json'), self.config)
    self.props.config_load()

    self.props.config_delete('user_name')

    self.assertNotIn('user_name', self.props)
    self.assertIn('project_name', self.props)
    self.assertIn('project_type', self.props)
    self.assertIn('project_features', self.props)

  def test_config_push_all(self):
    self.props.update(DATA)
    self.props.config_push()
    self.assertDictContainsSubset(DATA, self.props.config)

  def test_config_push_selective(self):
    self.props.update(DATA)
    self.props.config_push(['user_name'])
    self.assertIn('user_name', self.props.config)
    self.assertNotIn('project_name', self.props.config)
    self.assertNotIn('project_type', self.props.config)
    self.assertNotIn('project_features', self.props.config)
