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
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'], requires=['alpha'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_category_require_self_transitively(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'], requires=['echo'])
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory, features=['foxtrot'], requires=['alpha'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_self(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature, requires=['bravo'])
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_self_transitively(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'], requires=['foxtrot'])
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory, features=['foxtrot'], requires=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_own_category(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature, requires=['alpha'])
        self.register_feature_category_class(
            'alpha',
            FeatureCategory, features=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')


class FeatureCtrlTestSingularity(unittest.TestCase):

  def setUp(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory,
            features=['bravo', 'charlie', 'delta'],
            mono=True)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_class('golf', Feature)
        self.register_feature_class('hotel', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory,
            features=['foxtrot', 'golf', 'hotel'],
            mono=False)

    self.renv = create_runtime(RunnerBlah)
    self.renv.create_runner('runner')
    self.ctrl = self.renv.feature_ctrl

  @unittest.expectedFailure
  def test_fail_on_many_featuers_of_singular_category(self):
    self.ctrl.activate_features(['bravo', 'charlie', 'delta'])

  def test_no_fail_on_many_ftrs_multi_category(self):
    self.ctrl.activate_features(['foxtrot', 'golf', 'hotel'])


class FeatureCtrlTestActivationOrder(unittest.TestCase):

  def test_default_activates_all_defaults(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory,
            features=['bravo', 'charlie', 'delta'],
            defaults=['bravo', 'charlie', 'delta'],
            mono=False)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_class('golf', Feature)
        self.register_feature_class('hotel', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory,
            features=['foxtrot', 'golf', 'hotel'],
            defaults=['foxtrot', 'golf', 'hotel'],
            mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = sorted(['foxtrot', 'golf', 'hotel', 'bravo', 'charlie', 'delta'])
    ctrl.activate_features('default')
    self.assertEqual(expect, sorted(ctrl.get_active_features_names()))

  def test_category_activates_all_defaults(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory,
            features=['bravo', 'charlie', 'delta'],
            defaults=['bravo', 'charlie'],
            mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = sorted(['bravo', 'charlie'])
    ctrl.activate_features(['alpha'])
    self.assertEqual(expect, sorted(ctrl.get_active_features_names()))

  def test_sibling_feature_dependency(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature, requires=['charlie'])
        self.register_feature_class('bravo', Feature, requires=['delta'])
        self.register_feature_category_class(
            'alpha',
            FeatureCategory,
            features=['bravo', 'charlie', 'delta'],
            mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = ['charlie', 'delta', 'bravo']
    total_order, _ = ctrl.get_activation_order(['bravo'])
    self.assertEqual(expect, total_order)

  def test_category_depends_on_category_with_defaults(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory,
            features=['foxtrot'],
            defaults=['foxtrot'])
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory,
            features=['bravo'],
            defaults=['bravo'],
            requires=['echo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = ['foxtrot', 'bravo']
    total_order, _ = ctrl.get_activation_order(['alpha'])
    self.assertEqual(expect, total_order)

  @unittest.expectedFailure
  def test_category_depends_on_category_with_no_defaults(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class(
            'echo',
            FeatureCategory,
            features=['foxtrot'])
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha',
            FeatureCategory,
            features=['bravo'],
            defaults=['bravo'],
            requires=['echo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl
    ctrl.get_activation_order(['alpha'])
