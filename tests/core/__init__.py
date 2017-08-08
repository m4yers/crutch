def get_suite():
  import unittest
  import tests.core.features as features
  import tests.core.properties as properties
  import tests.core.replacements as replacements

  loader = unittest.defaultTestLoader
  suite = unittest.TestSuite()
  suite.addTest(loader.loadTestsFromModule(features))
  suite.addTest(loader.loadTestsFromModule(properties))
  suite.addTest(loader.loadTestsFromModule(replacements))

  return suite
