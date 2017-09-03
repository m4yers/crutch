import logging
import unittest

from mock import MagicMock

from crutch.core.runner import Runner, Runners
from crutch.core.runtime import RuntimeEnvironment
from crutch.core.features.basics import Feature, FeatureCategory

def create_runtime(runner):
  return RuntimeEnvironment(Runners({'runner': runner}))

def create_feature(*args, **kwargs):
  return MagicMock(Feature, wraps=Feature(*args, **kwargs))

def create_category(*args, **kwargs):
  return MagicMock(FeatureCategory, wraps=FeatureCategory(*args, **kwargs))

class FeatureCtrlReplProviderTest(unittest.TestCase):

  def test_generate(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo', 'charlie'], mono=False)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class('echo', features=['foxtrot'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')
    renv.feature_ctrl.activate_features(['bravo', 'charlie', 'foxtrot'])

    # Collect all the replacments
    renv.repl.fetch()

    self.assertTrue(renv.repl.get('project_feature_category_alpha'))
    self.assertTrue(renv.repl.get('project_feature_bravo'))
    self.assertTrue(renv.repl.get('project_feature_charlie'))
    self.assertTrue(renv.repl.get('project_feature_category_echo'))
    self.assertTrue(renv.repl.get('project_feature_foxtrot'))


class FeatureCtrlTestCircularDependencies(unittest.TestCase):

  @unittest.expectedFailure
  def test_category_require_self(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'], requires=['alpha'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_category_require_self_transitively(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'], requires=['echo'])
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class(
            'echo', features=['foxtrot'], requires=['alpha'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_self(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature, requires=['bravo'])
        self.register_feature_category_class('alpha', features=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_self_transitively(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'], requires=['foxtrot'])
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class(
            'echo', features=['foxtrot'], requires=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_require_own_category(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature, requires=['alpha'])
        self.register_feature_category_class('alpha', features=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

  @unittest.expectedFailure
  def test_feature_reattaching(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature, requires=['alpha'])
        self.register_feature_category_class('alpha', features=['bravo'])
        self.register_feature_category_class('echo', features=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')


class FeatureCtrlTestNames(unittest.TestCase):

  @unittest.expectedFailure
  def test_activate_unknown_names(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class('alpha', features=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')
    ctrl = renv.feature_ctrl
    ctrl.activate_features(['oscar'])

  @unittest.expectedFailure
  def test_deactivate_unknown_names(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class('alpha', features=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')
    ctrl = renv.feature_ctrl
    ctrl.deactivate_features(['oscar'])


class FeatureCtrlTestMono(unittest.TestCase):

  def setUp(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo', 'charlie', 'delta'], mono=True)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_class('golf', Feature)
        self.register_feature_class('hotel', Feature)
        self.register_feature_category_class(
            'echo', features=['foxtrot', 'golf', 'hotel'], mono=False)

    self.renv = create_runtime(RunnerBlah)
    self.renv.create_runner('runner')
    self.ctrl = self.renv.feature_ctrl

  @unittest.expectedFailure
  def test_fail_on_many_featuers_of_mono_category(self):
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
            features=['bravo', 'charlie', 'delta'],
            defaults=['bravo', 'charlie', 'delta'],
            mono=False)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_class('golf', Feature)
        self.register_feature_class('hotel', Feature)
        self.register_feature_category_class(
            'echo',
            features=['foxtrot', 'golf', 'hotel'],
            defaults=['foxtrot', 'golf', 'hotel'],
            mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = sorted(['foxtrot', 'golf', 'hotel', 'bravo', 'charlie', 'delta'])
    total_order, _ = ctrl.get_activation_order('default')
    self.assertEqual(expect, sorted(total_order))

  def test_category_activates_all_defaults(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature)
        self.register_feature_category_class(
            'alpha',
            features=['bravo', 'charlie', 'delta'],
            defaults=['bravo', 'charlie'],
            mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = sorted(['bravo', 'charlie'])
    total_order, _ = ctrl.get_activation_order(['alpha'])
    self.assertEqual(expect, sorted(total_order))

  def test_category_and_its_feature(self):
    """
    If features and their category is mentioned in the activation order only the
    features stay
    """
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo', 'charlie'], mono=True)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    total_order, _ = ctrl.get_activation_order(['alpha', 'bravo'])
    self.assertEqual(['bravo'], total_order)

  def test_category_and_its_feature_dep(self):
    """
    If features and their category is mentioned in the requires order only the
    features stay
    """
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'], defaults=['bravo'])
        self.register_feature_class(
            'foxtrot', Feature, requires=['alpha', 'bravo'])
        self.register_feature_category_class('echo', features=['foxtrot'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    total_order, _ = ctrl.get_activation_order(['foxtrot'])
    self.assertEqual(['bravo', 'foxtrot'], total_order)

  def test_sibling_feature_dependency(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature, requires=['charlie'])
        self.register_feature_class('bravo', Feature, requires=['delta'])
        self.register_feature_category_class(
            'alpha', features=['bravo', 'charlie', 'delta'], mono=False)

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
            'echo', features=['foxtrot'], defaults=['foxtrot'])
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'], defaults=['bravo'], requires=['echo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = ['foxtrot', 'bravo']
    total_order, _ = ctrl.get_activation_order(['alpha'])
    self.assertEqual(expect, total_order)

  def test_feature_depends_on_category_with_defaults(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('delta', Feature)
        self.register_feature_class('charlie', Feature, requires=['delta'])
        self.register_feature_class('bravo', Feature, requires=['charlie'])
        self.register_feature_category_class(
            'alpha',
            defaults=['bravo', 'charlie', 'delta'], features=['bravo'])
        self.register_feature_class('foxtrot', Feature, requires=['alpha'])
        self.register_feature_category_class('echo', features=['foxtrot'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = ['delta', 'charlie', 'bravo', 'foxtrot']
    total_order, _ = ctrl.get_activation_order(['foxtrot'])
    self.assertEqual(expect, total_order)

  def test_feature_activate_transitive_dependencies(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)

        self.register_feature_class('delta', Feature)
        self.register_feature_class('charlie', Feature, requires=['delta'])
        self.register_feature_class('bravo', Feature, requires=['charlie'])
        self.register_feature_category_class(
            'alpha',
            features=['bravo', 'charlie', 'delta'],
            defaults=['bravo', 'charlie', 'delta'])

        self.register_feature_class('foxtrot', Feature, requires=['bravo'])
        self.register_feature_category_class('echo', features=['foxtrot'])

        self.register_feature_class('juliet', Feature, requires=['foxtrot'])
        self.register_feature_category_class('india', features=['juliet'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = ['delta', 'charlie', 'bravo', 'foxtrot', 'juliet']
    total_order, _ = ctrl.get_activation_order(['juliet'])
    self.assertEqual(expect, total_order)

  @unittest.expectedFailure
  def test_category_depends_on_category_with_no_defaults(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_category_class('echo', features=['foxtrot'])
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'], defaults=['bravo'], requires=['echo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl
    ctrl.get_activation_order(['alpha'])

  @unittest.expectedFailure
  def test_fail_activate_feature_mono_twice(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo', 'charlie'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl
    ctrl.activate_features(['bravo'])
    ctrl.activate_features(['charlie'])

  @unittest.expectedFailure
  def test_fail_activate_category_twice(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'], defaults=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl
    ctrl.activate_features(['alpha'])
    ctrl.activate_features(['alpha'])


class FeatureCtrlTestDeactivationOrder(unittest.TestCase):

  def test_all_deactivates_all_active(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature)
        self.register_feature_category_class(
            'alpha',
            features=['bravo', 'charlie', 'delta'],
            defaults=['bravo', 'charlie', 'delta'],
            mono=False)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_class('golf', Feature)
        self.register_feature_class('hotel', Feature)
        self.register_feature_category_class(
            'echo',
            features=['foxtrot', 'golf', 'hotel'],
            defaults=['foxtrot', 'golf', 'hotel'],
            mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    expect = sorted(['golf', 'bravo', 'charlie', 'delta'])
    ctrl.activate_features(['alpha', 'golf'])
    total_order, _ = ctrl.deactivate_features('all')
    self.assertEqual(expect, sorted(total_order))

    self.assertFalse(ctrl.get_active_categories())
    self.assertFalse(ctrl.get_active_features())

  def test_category_deactivates_all_its_active_features(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_class('delta', Feature)
        self.register_feature_category_class(
            'alpha',
            features=['bravo', 'charlie', 'delta'],
            defaults=['bravo', 'charlie', 'delta'],
            mono=False)
        self.register_feature_class('foxtrot', Feature)
        self.register_feature_class('golf', Feature)
        self.register_feature_class('hotel', Feature)
        self.register_feature_category_class(
            'echo',
            features=['foxtrot', 'golf', 'hotel'],
            defaults=['foxtrot', 'golf', 'hotel'],
            mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    killed = sorted(['bravo', 'charlie', 'delta'])
    ctrl.activate_features('default')
    total_order, _ = ctrl.deactivate_features(['alpha'])
    self.assertEqual(killed, sorted(total_order))

    self.assertEqual(ctrl.get_active_categories_names(), ['echo'])
    alive = sorted(['foxtrot', 'golf', 'hotel'])
    self.assertEqual(sorted(ctrl.get_active_features_names()), alive)

  def test_deactivate_implicit_dependencies(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo', 'charlie'])
        self.register_feature_class(
            'foxtrot', Feature, requires=['bravo', 'charlie'])
        self.register_feature_category_class('echo', features=['foxtrot'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    ctrl.activate_features(['foxtrot'])
    total_order, _ = ctrl.deactivate_features(['foxtrot'])

    killed_ftrs = sorted(['foxtrot', 'bravo', 'charlie'])
    self.assertEqual(sorted(total_order), killed_ftrs)

    self.assertFalse(ctrl.get_active_categories_names())
    self.assertFalse(ctrl.get_active_features_names())

  def test_deactivate_implicit_dependencies_category(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_class('charlie', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo', 'charlie'],
            defaults=['bravo', 'charlie'])
        self.register_feature_class(
            'foxtrot', Feature, requires=['alpha'])
        self.register_feature_category_class('echo', features=['foxtrot'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    ctrl.activate_features(['foxtrot'])
    total_order, _ = ctrl.deactivate_features(['foxtrot'])

    killed_ftrs = sorted(['foxtrot', 'bravo', 'charlie'])
    self.assertEqual(sorted(total_order), killed_ftrs)

    self.assertFalse(ctrl.get_active_categories_names())
    self.assertFalse(ctrl.get_active_features_names())

  def test_deactivation_skip(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class(
            'alpha', features=['bravo'])
        self.register_feature_class(
            'foxtrot', Feature, requires=['bravo'])
        self.register_feature_category_class(
            'echo', features=['foxtrot'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    ctrl.activate_features(['foxtrot', 'bravo'])
    total_order, _ = ctrl.deactivate_features(['foxtrot'], skip=['bravo'])

    killed_ftrs = ['foxtrot']
    self.assertEqual(total_order, killed_ftrs)

    active_cats = ['alpha']
    self.assertEqual(ctrl.get_active_categories_names(), active_cats)

    active_ftrs = ['bravo']
    self.assertEqual(ctrl.get_active_features_names(), active_ftrs)

  def test_deactivate_skip_if_referenced_by_other(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class('alpha', features=['bravo'])
        self.register_feature_class('foxtrot', Feature, requires=['bravo'])
        self.register_feature_class('golf', Feature, requires=['bravo'])
        self.register_feature_category_class(
            'echo', features=['foxtrot', 'golf'], mono=False)

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    ctrl.activate_features(['foxtrot', 'golf'])
    total_order, _ = ctrl.deactivate_features(['foxtrot'])

    killed_ftrs = ['foxtrot']
    self.assertEqual(total_order, killed_ftrs)

    active_cats = sorted(['alpha', 'echo'])
    self.assertEqual(sorted(ctrl.get_active_categories_names()), active_cats)

    active_ftrs = sorted(['golf', 'bravo'])
    self.assertEqual(sorted(ctrl.get_active_features_names()), active_ftrs)

  @unittest.expectedFailure
  def test_deactivation_of_direct_dep(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', Feature)
        self.register_feature_category_class('alpha', features=['bravo'])
        self.register_feature_class('foxtrot', Feature, requires=['bravo'])
        self.register_feature_category_class('echo', features=['foxtrot'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    ctrl.activate_features(['foxtrot'])
    ctrl.deactivate_features(['bravo'])


class FeatureCtrlTestFtrCatLifecycle(unittest.TestCase):

  def test_lifecycle(self):
    class RunnerBlah(Runner):
      def __init__(self, renv):
        super(RunnerBlah, self).__init__(renv)
        self.register_feature_class('bravo', create_feature)
        self.register_feature_category_class(
            'alpha', create_category, features=['bravo'], defaults=['bravo'])

    renv = create_runtime(RunnerBlah)
    renv.create_runner('runner')

    ctrl = renv.feature_ctrl

    ctrl.activate_features(['alpha'], set_up=True)
    alpha = ctrl.get_active_category('alpha')
    alpha.set_up.assert_called_once()
    alpha.activate.assert_called_once()

    bravo = ctrl.get_active_feature('bravo')
    bravo.set_up.assert_called_once()
    bravo.activate.assert_called_once()

    ctrl.deactivate_features(['alpha'], tear_down=True)
    alpha.deactivate.assert_called_once()
    alpha.tear_down.assert_called_once()
    bravo.deactivate.assert_called_once()
    bravo.tear_down.assert_called_once()
