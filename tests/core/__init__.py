def get_suite():
  import unittest
  import tests.core.features as features
  import tests.core.properties as properties

  loader = unittest.defaultTestLoader
  suite = unittest.TestSuite()
  suite.addTest(loader.loadTestsFromModule(features))
  suite.addTest(loader.loadTestsFromModule(properties))

  return suite
