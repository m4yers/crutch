def get_suite():
  import unittest
  import tests.core.menu.menu as menu

  loader = unittest.defaultTestLoader
  suite = unittest.TestSuite()
  suite.addTest(loader.loadTestsFromModule(menu))

  return suite
