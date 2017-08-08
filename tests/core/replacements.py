import unittest

from crutch.core.replacements import GenerativeReplacementsProvider, Replacements

class GenerativeProvider(GenerativeReplacementsProvider):

  def __init__(self, mod):
    GenerativeReplacementsProvider.__init__(self)
    self.mod = mod

  def generate(self):
    self.data = dict()
    self.update(self.mod)
    return self.data

class ReplacementsTest(unittest.TestCase):

  def test_static(self):
    repl = Replacements()
    self.assertFalse(repl)

    stat = repl.add_provider('provider', dict())
    stat['key'] = 'value'
    self.assertNotIn('key', repl)

    repl.fetch()
    self.assertIn('key', repl)
    self.assertEqual(repl['key'], 'value')

    data = dict()
    data.update(repl)
    self.assertIn('key', data)
    self.assertEqual(data['key'], 'value')

    del stat['key']
    self.assertIn('key', repl)

    repl.fetch()
    self.assertNotIn('key', repl)

  def test_generator(self):
    repl = Replacements()

    gen = dict()
    gen = repl.add_provider('gen', GenerativeReplacementsProvider(gen))
    gen['key'] = 'value'
    self.assertNotIn('key', repl)

    repl.fetch()
    self.assertIn('key', repl)
    self.assertEqual(repl['key'], 'value')

    del gen['key']
    gen['blah'] = 'ooooo'
    self.assertIn('key', repl)

    repl.fetch()
    self.assertNotIn('key', repl)
    self.assertIn('blah', repl)
    self.assertEqual(repl['blah'], 'ooooo')
