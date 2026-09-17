import os
import tempfile
import unittest

from automations.linguistic_bits import СorpusDocument, LinguisticItem, Paragraph, Sentence, SentenceItemType
from automations.vert_io import VertIO


def word(text: str, glue_next: bool = False) -> LinguisticItem:
    return LinguisticItem(text, SentenceItemType.Word, glue_next)


def punctuation(text: str, glue_next: bool = False) -> LinguisticItem:
    return LinguisticItem(text, SentenceItemType.Punctuation, glue_next)


def line_break() -> LinguisticItem:
    return LinguisticItem(None, SentenceItemType.LineBreak)


class TestWriteText(unittest.TestCase):
    def write_text(self, document: СorpusDocument) -> str:
        handle, path = tempfile.mkstemp(suffix=".txt")
        os.close(handle)
        try:
            VertIO.write_text(document, path)
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        finally:
            os.remove(path)

    def test_paragraph_per_line_with_glue(self):
        document = СorpusDocument(
            paragraphs=[
                Paragraph(
                    sentences=[
                        Sentence(items=[word("Я"), word("стары", glue_next=True), punctuation(","), word("я"), word("нават"), word("стары", glue_next=True), punctuation(".")]),
                        Sentence(items=[word("Вітаю"), word("сьвет", glue_next=True), punctuation("!")]),
                    ]
                ),
                Paragraph(sentences=[Sentence(items=[word("Наступны"), word("параграф", glue_next=True), punctuation(".")])]),
            ]
        )

        self.assertEqual(self.write_text(document), "Я стары, я нават стары. Вітаю сьвет!\nНаступны параграф.\n")

    def test_line_break_inside_paragraph(self):
        document = СorpusDocument(
            paragraphs=[
                Paragraph(
                    sentences=[
                        Sentence(items=[word("Першы"), word("радок"), line_break(), word("другі"), word("радок", glue_next=True), punctuation(".")]),
                    ]
                )
            ]
        )

        # Пасля пераходу на новы радок прабела быць не павінна
        self.assertEqual(self.write_text(document), "Першы радок\nдругі радок.\n")

    def test_trailing_line_break_does_not_add_empty_line(self):
        document = СorpusDocument(paragraphs=[Paragraph(sentences=[Sentence(items=[word("Слова"), line_break()])])])

        self.assertEqual(self.write_text(document), "Слова\n")

    def test_unknown_item_type_raises(self):
        item = word("Слова")
        item.type = "нешта невядомае"
        document = СorpusDocument(paragraphs=[Paragraph(sentences=[Sentence(items=[item])])])

        with self.assertRaises(ValueError):
            self.write_text(document)


if __name__ == "__main__":
    unittest.main()
