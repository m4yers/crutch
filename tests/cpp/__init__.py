def get_suite():
  import unittest

  loader = unittest.defaultTestLoader
  suite = unittest.TestSuite()

  import tests.cpp.new as new
  suite.addTest(loader.loadTestsFromModule(new))

  return suite
