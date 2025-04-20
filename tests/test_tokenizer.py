import unittest
from automations.tokenizer import Tokenizer, Token, TokenType

class TestTokenizer(unittest.TestCase):
    def setUp(self):
        self.tokenizer = Tokenizer()

    def test_simple_sentence(self):
        text = "Вітаю сьвет!"
        tokens = self.tokenizer.parse(text)
        
        expected_tokens = [
            Token("Вітаю", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("сьвет", TokenType.Word),
            Token("!", TokenType.Tail),
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
            Token("Варʼяты", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("і", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("Бамжы", TokenType.Word)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

    def test_complex_sentence(self):
        text = "  Я стары, я нават вельмі стары чалавек."
        tokens = self.tokenizer.parse(text)

        expected_tokens = [
            Token("Я", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("стары", TokenType.Word),
            Token(", ", TokenType.Tail),
            Token("я", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("нават", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("вельмі", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("стары", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("чалавек", TokenType.Word),
            Token(".", TokenType.Tail),
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
            Token("- ", TokenType.Tail),
            Token("Адно", TokenType.Word),
            Token(", ", TokenType.Tail),
            Token("слова", TokenType.Word),
            Token("...", TokenType.Tail),
            Token(None, TokenType.SentenceSeparator),
            Token(" ", TokenType.Tail),
            Token("А", TokenType.Word),
            Token(": ", TokenType.Tail),
            Token("потым", TokenType.Word),
            Token(" ?", TokenType.Tail),
            Token(None, TokenType.SentenceSeparator),
            Token(" ", TokenType.Tail),
            Token("123", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("мо", TokenType.Word),
            Token("'' '", TokenType.Tail),
            Token("ак", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("зʼява", TokenType.Word)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

    def test_multiline_text(self):
        text = "Хто піпку ку\u00B4рыць, хто сьмяецца,\nА іншы песьню бурудзіць."
        tokens = self.tokenizer.parse(text)
        
        expected_tokens = [
            Token("Хто", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("піпку", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("курыць", TokenType.Word),
            Token(", ", TokenType.Tail),
            Token("хто", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("сьмяецца", TokenType.Word),
            Token(",", TokenType.Tail),
            Token(None, TokenType.LineBreak),
            Token("А", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("іншы", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("песьню", TokenType.Word),
            Token(" ", TokenType.Tail),
            Token("бурудзіць", TokenType.Word),
            Token(".", TokenType.Tail),
            Token(None, TokenType.SentenceSeparator)
        ]
        
        self.assertEqual(len(tokens), len(expected_tokens))
        for actual, expected in zip(tokens, expected_tokens):
            self.assertEqual(actual.text, expected.text)
            self.assertEqual(actual.type, expected.type)

if __name__ == '__main__':
    unittest.main() 