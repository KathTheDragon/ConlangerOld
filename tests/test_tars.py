import unittest

from context import conlanger


class TestMainChange(unittest.TestCase):

    def test_standard_change(self):
        rule = conlanger.sce.Rule(rule='a>b')
        word = conlanger.core.Word(lexeme='a')
        changed_word = str(rule.apply(word))
        self.assertEqual(changed_word, 'b')

    def test_addition_change(self):
        rule = conlanger.sce.Rule(rule='+b/_#')
        word = conlanger.core.Word(lexeme='a')
        changed_word = str(rule.apply(word))
        self.assertEqual(changed_word, 'ab')

    def test_subtraction_change(self):
        rule = conlanger.sce.Rule(rule='-b')
        word = conlanger.core.Word(lexeme='ab')
        changed_word = str(rule.apply(word))
        self.assertEqual(changed_word, 'a')


suite = unittest.TestLoader().loadTestsFromTestCase(TestMainChange)
unittest.TextTestRunner(verbosity=2).run(suite)
