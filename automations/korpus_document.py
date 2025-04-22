from enum import Enum
from dataclasses import dataclass
from typing import List, Type, TypeVar, Generic
import re

T = TypeVar('T')

@dataclass
class Sentence(Generic[T]):
    items: List[T]

@dataclass
class Paragraph(Generic[T]):
    sentences: List[Sentence[T]]

@dataclass
class KorpusDocument(Generic[T]):
    title: str
    author: str | None
    language: str | None
    publication_date: str | None
    paragraphs: List[Paragraph[T]] = None

    def __post_init__(self):
        if self.paragraphs is None:
            self.paragraphs = []

class SentenceItemType(Enum):
    Word = 1
    Punctuation = 2
    LineBreak = 4

@dataclass
class SentenceItem:
    def __init__(self, text: str, type: SentenceItemType, glue_next = False):
        self.text = text
        self.type = type
        self.glue_next = glue_next

    text: str
    type: SentenceItemType
    glue_next: bool


TLemmaForm = TypeVar('TLF', bound='LemmaForm')

@dataclass
class LemmaForm:
    parsing_re = re.compile(r'^\s*(\d+)([a-z]?)\.(.*)\s*$')

    def __init__(self, pardigm_id: int, variant_id = 'a', form_tag: str = None):
        self.paradigm_id = pardigm_id
        self.variant_id = variant_id
        self.form_tag = form_tag

    paradigm_id: int
    variant_id: str
    form_tag: str

    def __str__(self) -> str:
        return f"{self.paradigm_id}{self.variant_id}.{self.form_tag}"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def from_string(cls: Type[TLemmaForm], string_repr: str) -> TLemmaForm | None:
        if not string_repr:
            return None
        
        match = LemmaForm.parsing_re.match(string_repr)
        
        if not match:
            return None

        paradigm_id = int(match.group(1))
        variant_id = match.group(2) or 'a'
        form_tag = match.group(3) or None
        
        return cls(paradigm_id, variant_id, form_tag)


@dataclass
class LinguisticItem(SentenceItem):
    def __init__(self, sentence_item: SentenceItem):
        self.text = sentence_item.text
        self.type = sentence_item.type
        self.glue_next = sentence_item.glue_next

    lemma_form_id: LemmaForm
    lemma: str
    linguistic_tags: str
    comment: str
    metadata: object