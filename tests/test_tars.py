import unittest

from context import conlanger


class TestMainChange(unittest.TestCase):

    def test_standard_change(self):
        rule = conlanger.sce.Rule(rule='a>b')
        self.assertEqual(rule.apply('a'), 'b')

    def test_addition_change(self):
        rule = conlanger.sce.Rule(rule='+b/_#')
        self.assertEqual(rule.apply('a'), 'ab')

    def test_subtraction_change(self):
        rule = conlanger.sce.Rule(rule='-b')
        self.assertEqual(rule.apply('ab'), 'a')


suite = unittest.TestLoader().loadTestsFromTestCase(TestMainChange)
unittest.TextTestRunner(verbosity=2).run(suite)
