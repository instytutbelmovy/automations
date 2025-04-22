import unittest
from automations.tokenizer import Token, TokenType
from automations.sentencer import Sentencer, SentenceItem, SentenceItemType

class TestSentencer(unittest.TestCase):
    def setUp(self):
        self.sentencer = Sentencer()

    def test_simple_sentence(self):
        tokens = [
            Token("Вітаю", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("сьвет", TokenType.AlphaNumeric),
            Token("!", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator),
        ]

        sentences = self.sentencer.to_sentences(tokens)
        
        expected_sentences = [
            [
                SentenceItem("Вітаю", SentenceItemType.Word),
                SentenceItem("сьвет", SentenceItemType.Word, glue_next = True),
                SentenceItem("!", SentenceItemType.Punctuation),
            ]
        ]
        
        self.assertEqual(len(sentences), len(expected_sentences))
        for actual_sentence, expected_sentence in zip(sentences, expected_sentences):
            self.assertEqual(len(actual_sentence), len(expected_sentence))
            for actual, expected in zip(actual_sentence, expected_sentence):
                self.assertEqual(actual.text, expected.text)
                self.assertEqual(actual.type, expected.type)
                self.assertEqual(actual.glue_next, expected.glue_next)

    def test_multiple_words(self):
        tokens = [
            Token("Варʼяты", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("і", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("Бамжы", TokenType.AlphaNumeric),
        ]

        sentences = self.sentencer.to_sentences(tokens)
        
        expected_sentences = [
            [
                SentenceItem("Варʼяты", SentenceItemType.Word),
                SentenceItem("і", SentenceItemType.Word),
                SentenceItem("Бамжы", SentenceItemType.Word)
            ]
        ]
        
        self.assertEqual(len(sentences), len(expected_sentences))
        for actual_sentence, expected_sentence in zip(sentences, expected_sentences):
            self.assertEqual(len(actual_sentence), len(expected_sentence))
            for actual, expected in zip(actual_sentence, expected_sentence):
                self.assertEqual(actual.text, expected.text)
                self.assertEqual(actual.type, expected.type)
                self.assertEqual(actual.glue_next, expected.glue_next)

    def test_complex_sentence(self):
        tokens = [
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
            Token(None, TokenType.SentenceSeparator),
        ]

        sentences = self.sentencer.to_sentences(tokens)
        
        expected_sentences = [
            [
                SentenceItem("Я", SentenceItemType.Word),
                SentenceItem("стары", SentenceItemType.Word, glue_next = True),
                SentenceItem(",", SentenceItemType.Punctuation),
                SentenceItem("я", SentenceItemType.Word),
                SentenceItem("нават", SentenceItemType.Word),
                SentenceItem("вельмі", SentenceItemType.Word),
                SentenceItem("стары", SentenceItemType.Word),
                SentenceItem("чалавек", SentenceItemType.Word, glue_next = True),
                SentenceItem(".", SentenceItemType.Punctuation),
            ]
        ]
        
        self.assertEqual(len(sentences), len(expected_sentences))
        for actual_sentence, expected_sentence in zip(sentences, expected_sentences):
            self.assertEqual(len(actual_sentence), len(expected_sentence))
            for actual, expected in zip(actual_sentence, expected_sentence):
                self.assertEqual(actual.text, expected.text)
                self.assertEqual(actual.type, expected.type)
                self.assertEqual(actual.glue_next, expected.glue_next)

    def test_special_characters(self):
        tokens = [
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
            Token("зʼява", TokenType.AlphaNumeric),
        ]

        sentences = self.sentencer.to_sentences(tokens)
        
        expected_sentences = [
            [
                SentenceItem("-", SentenceItemType.Punctuation),
                SentenceItem("Адно", SentenceItemType.Word, glue_next = True),
                SentenceItem(",", SentenceItemType.Punctuation),
                SentenceItem("слова", SentenceItemType.Word, glue_next = True),
                SentenceItem("...", SentenceItemType.Punctuation),
            ],
            [
                SentenceItem("А", SentenceItemType.Word, glue_next = True),
                SentenceItem(":", SentenceItemType.Punctuation),
                SentenceItem("потым", SentenceItemType.Word),
                SentenceItem("?", SentenceItemType.Punctuation),
            ],
            [
                SentenceItem("123", SentenceItemType.Word),
                SentenceItem("мо", SentenceItemType.Word, glue_next = True),
                SentenceItem("'' '", SentenceItemType.Punctuation, glue_next = True),
                SentenceItem("ак", SentenceItemType.Word),
                SentenceItem("зʼява", SentenceItemType.Word)
            ]
        ]
        
        self.assertEqual(len(sentences), len(expected_sentences))
        for actual_sentence, expected_sentence in zip(sentences, expected_sentences):
            self.assertEqual(len(actual_sentence), len(expected_sentence))
            for actual, expected in zip(actual_sentence, expected_sentence):
                self.assertEqual(actual.text, expected.text)
                self.assertEqual(actual.type, expected.type)
                self.assertEqual(actual.glue_next, expected.glue_next)

    def test_multiline_text(self):
        tokens = [
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
            Token(None, TokenType.SentenceSeparator),
        ]

        sentences = self.sentencer.to_sentences(tokens)
        
        expected_sentences = [
            [
                SentenceItem("Хто", SentenceItemType.Word),
                SentenceItem("піпку", SentenceItemType.Word),
                SentenceItem("курыць", SentenceItemType.Word, glue_next = True),
                SentenceItem(",", SentenceItemType.Punctuation),
                SentenceItem("хто", SentenceItemType.Word),
                SentenceItem("сьмяецца", SentenceItemType.Word, glue_next = True),
                SentenceItem(",", SentenceItemType.Punctuation),
                SentenceItem(None, SentenceItemType.LineBreak),
                SentenceItem("А", SentenceItemType.Word),
                SentenceItem("іншы", SentenceItemType.Word),
                SentenceItem("песьню", SentenceItemType.Word),
                SentenceItem("бурудзіць", SentenceItemType.Word, glue_next = True),
                SentenceItem(".", SentenceItemType.Punctuation),
            ]
        ]
        
        self.assertEqual(len(sentences), len(expected_sentences))
        for actual_sentence, expected_sentence in zip(sentences, expected_sentences):
            self.assertEqual(len(actual_sentence), len(expected_sentence))
            for actual, expected in zip(actual_sentence, expected_sentence):
                self.assertEqual(actual.text, expected.text)
                self.assertEqual(actual.type, expected.type)
                self.assertEqual(actual.glue_next, expected.glue_next)

    def test_poem(self):
        tokens = [
            Token("Цемра", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("здушыла", TokenType.AlphaNumeric),
            Token(None, TokenType.LineBreak),
            Token("Цеплыню", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("скрыпічых", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("таноў", TokenType.AlphaNumeric),
            Token(".", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator),
            Token(None, TokenType.LineBreak),
            Token("Калі", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("двое", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("навек", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("разлучыліся", TokenType.AlphaNumeric),
            Token(",", TokenType.NonAlphaNumeric),
            Token(None, TokenType.LineBreak),
            Token("То", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("не", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("трэба", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("пяшчоты", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("і", TokenType.AlphaNumeric),
            Token(" ", TokenType.NonAlphaNumeric),
            Token("слоў", TokenType.AlphaNumeric),
            Token(".", TokenType.NonAlphaNumeric),
            Token(None, TokenType.SentenceSeparator),
        ]

        sentences = self.sentencer.to_sentences(tokens)
        
        expected_sentences = [
            [
                SentenceItem("Цемра", SentenceItemType.Word),
                SentenceItem("здушыла", SentenceItemType.Word),
                SentenceItem(None, SentenceItemType.LineBreak),
                SentenceItem("Цеплыню", SentenceItemType.Word),
                SentenceItem("скрыпічых", SentenceItemType.Word),
                SentenceItem("таноў", SentenceItemType.Word, glue_next=True),
                SentenceItem(".", SentenceItemType.Punctuation),
            ],
            [
                SentenceItem("Калі", SentenceItemType.Word),
                SentenceItem("двое", SentenceItemType.Word),
                SentenceItem("навек", SentenceItemType.Word),
                SentenceItem("разлучыліся", SentenceItemType.Word, glue_next=True),
                SentenceItem(",", SentenceItemType.Punctuation),
                SentenceItem(None, SentenceItemType.LineBreak),
                SentenceItem("То", SentenceItemType.Word),
                SentenceItem("не", SentenceItemType.Word),
                SentenceItem("трэба", SentenceItemType.Word),
                SentenceItem("пяшчоты", SentenceItemType.Word),
                SentenceItem("і", SentenceItemType.Word),
                SentenceItem("слоў", SentenceItemType.Word, glue_next=True),
                SentenceItem(".", SentenceItemType.Punctuation),
            ]
        ]
        
        self.assertEqual(len(sentences), len(expected_sentences))
        for actual_sentence, expected_sentence in zip(sentences, expected_sentences):
            self.assertEqual(len(actual_sentence), len(expected_sentence))
            for actual, expected in zip(actual_sentence, expected_sentence):
                self.assertEqual(actual.text, expected.text)
                self.assertEqual(actual.type, expected.type)
                self.assertEqual(actual.glue_next, expected.glue_next)

if __name__ == '__main__':
    unittest.main() 