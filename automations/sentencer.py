from typing import List
from .tokenizer import Token, TokenType
from .linguistic_bits import SentenceItem, SentenceItemType


class Sentencer:
    def __init__(self):
        pass

    def to_sentences(self, tokens: List[Token]) -> List[List[SentenceItem]]:
        result = []
        current_sentence = []
        next_glueable = False

        for token in tokens:
            if token.type == TokenType.SentenceSeparator:
                next_glueable = False
                if current_sentence:
                    result.append(current_sentence)
                    current_sentence = []
                continue

            if token.type == TokenType.LineBreak:
                next_glueable = False
                if current_sentence:
                    current_sentence.append(SentenceItem(None, SentenceItemType.LineBreak))
                continue

            if token.type == TokenType.AlphaNumeric:
                if next_glueable:
                    current_sentence[-1].glue_next = True
                current_sentence.append(SentenceItem(token.text, SentenceItemType.Word))
                next_glueable = True
            elif token.type == TokenType.NonAlphaNumeric:
                if next_glueable and token.text and not token.text[0].isspace():
                    current_sentence[-1].glue_next = True
                next_glueable = token.text and not token.text[-1].isspace()
                stripped_text = token.text.strip()
                if stripped_text:
                    current_sentence.append(SentenceItem(stripped_text, SentenceItemType.Punctuation))

        if current_sentence:
            result.append(current_sentence)

        return result
