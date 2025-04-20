import unittest
from automations.tokenizer import Tokenizer, Token, TokenType

class TestTokenizer(unittest.TestCase):
    def setUp(self):
        self.tokenizer = Tokenizer()

    def test_simple_sentence(self):
        text = "Вітаю сьвет!"
        tokens = self.tokenizer.parse(text)
        
        expected_tokens = [
            Token("Вітаю", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("сьвет", TokenType.AlphaNumeric),
            Token("!", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

    def test_multiple_words(self):
        text = "Вар'яты і Бамжы  "
        tokens = self.tokenizer.parse(text)
        
        expected_tokens = [
            Token("Варʼяты", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("і", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("Бамжы", TokenType.AlphaNumeric)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

    def test_complex_sentence(self):
        text = "  Я стары, я нават вельмі стары чалавек."
        tokens = self.tokenizer.parse(text)

        expected_tokens = [
            Token("Я", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("стары", TokenType.AlphaNumeric),
            Token(", ", TokenType.NonAlphaNumeric),
            Token("я", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("нават", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("вельмі", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("стары", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("чалавек", TokenType.AlphaNumeric),
            Token(".", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

    def test_special_characters(self):
        text = "- Адно, слова... А: потым ? 123 мо'' 'ак з'ява"
        tokens = self.tokenizer.parse(text)

        expected_tokens = [
            Token("- ", TokenType.NonAlphaNumeric),
            Token("Адно", TokenType.AlphaNumeric),
            Token(", ", TokenType.NonAlphaNumeric),
            Token("слова", TokenType.AlphaNumeric),
            Token("...", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("А", TokenType.AlphaNumeric),
            Token(": ", TokenType.NonAlphaNumeric),
            Token("потым", TokenType.AlphaNumeric),
            Token(" ?", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("123", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("мо", TokenType.AlphaNumeric),
            Token("'' '", TokenType.NonAlphaNumeric),
            Token("ак", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("зʼява", TokenType.AlphaNumeric)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

    def test_multiline_text(self):
        text = "Хто піпку ку\u00B4рыць, хто сьмяецца,\nА іншы песьню бурудзіць."
        tokens = self.tokenizer.parse(text)
        
        expected_tokens = [
            Token("Хто", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("піпку", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("курыць", TokenType.AlphaNumeric),
            Token(", ", TokenType.NonAlphaNumeric),
            Token("хто", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("сьмяецца", TokenType.AlphaNumeric),
            Token(",", TokenType.NonAlphaNumeric),
            Token(None, TokenType.LineBreak),
            Token("А", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("іншы", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("песьню", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("бурудзіць", TokenType.AlphaNumeric),
            Token(".", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

if __name__ == '__main__':
    unittest.main() 