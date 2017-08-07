def get_suite():
  import unittest
  import tests.core.features as features
  return unittest.defaultTestLoader.loadTestsFromModule(features)
