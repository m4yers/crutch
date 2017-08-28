def get_suite():
  import unittest

  loader = unittest.defaultTestLoader
  suite = unittest.TestSuite()

  import tests.core.features.ctrl as ctrl
  suite.addTest(loader.loadTestsFromModule(ctrl))

  import tests.core.properties as properties
  suite.addTest(loader.loadTestsFromModule(properties))

  import tests.core.replacements as replacements
  suite.addTest(loader.loadTestsFromModule(replacements))

  import tests.core.menu as menu
  suite.addTest(loader.loadTestsFromModule(menu))

  return suite
