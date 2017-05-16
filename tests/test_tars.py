import unittest

from context import conlanger


class TestMainChange(unittest.TestCase):

    def test_standard_change(self):
        rule = conlanger.sce.Rule(rule='a>b')
        word = conlanger.core.Word(lexeme='a')
        self.assertEqual(rule.apply(word), 'b')

    def test_addition_change(self):
        rule = conlanger.sce.Rule(rule='+b/_#')
        word = conlanger.core.Word(lexeme='a')
        self.assertEqual(rule.apply(word), 'ab')

    def test_subtraction_change(self):
        rule = conlanger.sce.Rule(rule='-b')
        word = conlanger.core.Word(lexeme='ab')
        self.assertEqual(rule.apply(word), 'a')


suite = unittest.TestLoader().loadTestsFromTestCase(TestMainChange)
unittest.TextTestRunner(verbosity=2).run(suite)
