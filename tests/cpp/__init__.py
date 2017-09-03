def get_suite():
  import unittest

  loader = unittest.defaultTestLoader
  suite = unittest.TestSuite()

  import tests.cpp.integration as integration
  suite.addTest(loader.loadTestsFromModule(integration))

  return suite
