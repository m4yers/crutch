import unittest

from crutch.core.runner import Runner, Runners
from crutch.core.runtime import RuntimeEnvironment
from crutch.core.features.basics import Feature, FeatureCategory

def create_runtime(runner):
  return RuntimeEnvironment(Runners({'runner': runner}))

class FeatureCtrlTestCircularDependencies(unittest.TestCase):

  @unittest.expectedFailure
  def test_category_require_self(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'], requires=['alpha'])
        self.register_feature_class('bravo', Feature)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_category_require_self_transitively(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'], requires=['echo'])
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory, features=['foxtrot'], requires=['alpha'])
        self.register_feature_class('foxtrot', Feature)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_self(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'])
        self.register_feature_class('bravo', Feature, requires=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_self_transitively(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'], requires=['foxtrot'])
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory, features=['foxtrot'], requires=['bravo'])
        self.register_feature_class('foxtrot', Feature)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_own_category(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'])
        self.register_feature_class('bravo', Feature, requires=['alpha'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')
