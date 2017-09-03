from __future__ import unicode_literals
from __future__ import print_function

import unittest
import shutil
import tempfile
import os

from crutch import create_driver

THIS_FOLDER = os.path.abspath(os.path.dirname(__file__))


class NewCPPTestCleanProjectFolder(unittest.TestCase):

  def test_clean_folder(self):
    folder = tempfile.mkdtemp()
    print(folder)
    driver = create_driver(['new', 'cpp', '--directory', folder])
    code = driver.run()

    self.assertEqual(code, 0)
    self.assertTrue(os.path.exists(os.path.join(folder, 'CMakeLists.txt')))
    self.assertTrue(os.path.exists(os.path.join(folder, 'include')))
    self.assertTrue(os.path.exists(os.path.join(folder, 'src')))

    shutil.rmtree(folder)


if __name__ == '__main__':
  unittest.main()
