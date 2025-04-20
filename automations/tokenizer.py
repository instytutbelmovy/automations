from enum import Enum
from dataclasses import dataclass
from typing import List
from automations.normalizer import Normalizer


class TokenType(Enum):
    Word = 1
    Tail = 2
    SentenceSeparator = 3
    LineBreak = 4

@dataclass
class Token:
    def __init__(self, text: str, type: TokenType):
        self.text = text
        self.type = type

    text: str
    type: TokenType


class Tokenizer:
    def __init__(self, process_simple_html: bool = False):
        self._normalizer = Normalizer()
        self._process_simple_html = process_simple_html
    
    def parse(self, line: str) -> List[Token]:
        result = []
        current_word = []
        current_tail = []

        def append_znak(char: str):
            nonlocal current_word
            nonlocal current_tail
            if not current_tail:
                while current_word:
                    last_char = current_word[-1]
                    if self._normalizer.is_apostraf(last_char) or last_char == self._normalizer.DASH:
                        current_word.pop()
                        current_tail.insert(0, last_char)
                    else:
                        break
            current_tail.append(char)

        def close_word():
            nonlocal current_word
            nonlocal current_tail
            if current_word:
                word = ''.join(current_word)
                normalized_word = self._normalizer.znak_normalized(word)
                result.append(Token(normalized_word, TokenType.Word))

            if current_tail:
                result.append(Token(''.join(current_tail), TokenType.Tail))

            current_word = []
            current_tail = []


        last_non_space_index = len(line) - 1
        while 0 <= last_non_space_index and line[last_non_space_index].isspace():
            last_non_space_index -= 1 

        i = 0
        while i < len(line) and line[i].isspace():
            i += 1 
        while i <= last_non_space_index:
            char = line[i]

            if char == '\n':
                close_word()
                result.append(Token(None, TokenType.LineBreak))

            elif char in '.?!':
                if not current_word and not current_tail and result and result[-1].type == TokenType.SentenceSeparator:
                    prev = result[-2]
                    if prev.type == TokenType.Tail:
                        prev.text += char
                else:
                    append_znak(char)
                    close_word()
                    result.append(Token(None, TokenType.SentenceSeparator))


            #elif char == '<' and self._process_simple_html:
            #    close_word()
            #    tag = _parse_inline_tag(line, i)
            #    result.add(InlineTag(tag))
            #    i += len(tag) - 1

            #elif char == '&' and self._process_simple_html:
            #    char = _parse_char_name_or_number(line, i)
            #    while i < len(line) and line[i] != ';':
            #        i += 1
            #    if char == '\0':
            #        i += 1
            #        continue

            elif self._normalizer.is_apostraf(char) or char == self._normalizer.DASH:
                if current_word and not current_tail:
                    current_word.append(char)
                else:
                    append_znak(char)

            elif self._normalizer.is_letter(char) or char in '[]':
                if current_tail:
                    close_word()
                current_word.append(char)

            else:
                append_znak(char)

            i += 1

        close_word()


#        def _parse_inline_tag(self, text: str, start: int) -> str:
#            end = text.find('>', start)
#            if end == -1:
#                end = len(text)
#            return text[start:end + 1]
#        
#        def _parse_char_name_or_number(self, text: str, start: int) -> str:
#            if start + 1 >= len(text):
#                return '\0'
#            
#            if text[start + 1] == '#':
#                start += 2
#            else:
#                start += 1
#            
#            end = text.find(';', start)
#            if end == -1:
#                return '\0'
#            
#            name = text[start:end]
#            if text[start - 1] == '#':
#                return chr(int(name))
#            
#            char_map = {
#                "nbsp": " ",
#                "oacute": "ó",
#                "quot": '"',
#                "lt": "<",
#                "gt": ">",
#                "laquo": "«",
#                "raquo": "»",
#                "bdquo": "„",
#                "ldquo": "“",
#                "rdquo": "”",
#                "ndash": "–",
#                "mdash": "—",
#                "rsquo": "\u2019",
#                "shy": "\0",
#                "amp": "&"
#            }
#            
#            return char_map.get(name, '\0')


        return result
