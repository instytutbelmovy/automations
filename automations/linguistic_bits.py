import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Type, TypeVar, Generic, Dict, Optional
import re

logger = logging.getLogger(__name__)


T = TypeVar("T")


@dataclass
class Sentence(Generic[T]):
    items: List[T]


@dataclass
class Paragraph(Generic[T]):
    sentences: List[Sentence[T]]


@dataclass
class KorpusDocument(Generic[T]):
    n: int | None = None
    title: str | None = None
    author: str | None = None
    language: str | None = None
    publication_date: str | None = None
    url: str | None = None
    type: str | None = None
    style: str | None = None
    paragraphs: List[Paragraph[T]] = field(default_factory=list)

    def __post_init__(self):
        if self.paragraphs is None:
            self.paragraphs = []


class SentenceItemType(Enum):
    Word = 1
    Punctuation = 2
    LineBreak = 4


@dataclass
class SentenceItem:
    """Слова, ці іншы структурны элемэнт, атрыманы пасьля разбору тэксту з дакумэнта-крыніцы"""

    def __init__(self, text: str, type: SentenceItemType, glue_next=False):
        self.text = text
        self.type = type
        self.glue_next = glue_next

    text: str
    type: SentenceItemType
    glue_next: bool


TParadigmaFormId = TypeVar("TLFI", bound="ParadigmaFormId")

POS_MAPPING = {
    "N": "NOUN",
    "A": "ADJ",
    "M": "NUM",
    "S": "PRON",
    "V": "VERB",
    "P": "ADJ",
    "R": "ADV",
    "C": "CCONJ",
    "I": "ADP",
    "E": "PART",
    "Y": "INTJ",
    "Z": "AUX",
    "W": "AUX",
    "F": "X",
}


@dataclass
class ParadigmaFormId:
    """Ідэнтыфікатар парадыгмы і формы з граматычнай базы. Але можа быць ня поўным, прыкладам калі ўдалося вызначыць парадыгму, але ня форму"""

    PARSING_RE = re.compile(r"^\s*(\d+)([a-z]?)(?:\.(.*))?\s*$")

    def __init__(self, pardigm_id: int, variant_id="a", form_tag: str = None):
        self.paradigm_id = pardigm_id
        self.variant_id = variant_id
        self.form_tag = form_tag

    paradigm_id: int
    variant_id: str
    form_tag: str

    def __str__(self) -> str:
        return f"{self.paradigm_id}{self.variant_id or ''}.{self.form_tag or ''}"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def from_string(string_repr: str) -> Optional["ParadigmaFormId"]:
        if not string_repr:
            return None

        match = ParadigmaFormId.PARSING_RE.match(string_repr)

        if not match:
            return None

        (paradigm_id_str, variant_id, form_tag) = match.groups()
        paradigm_id = int(paradigm_id_str)

        variant_id = variant_id or None
        form_tag = form_tag or None

        return ParadigmaFormId(paradigm_id, variant_id, form_tag)

    @staticmethod
    def clone(other: "ParadigmaFormId") -> "ParadigmaFormId":
        return ParadigmaFormId(other.paradigm_id, other.variant_id, other.form_tag)

    def intersect_with(self, other: Optional["ParadigmaFormId"]) -> Optional["ParadigmaFormId"]:
        if other is None:
            return None

        intersected_paradigm_id = self.paradigm_id if self.paradigm_id == other.paradigm_id else None
        intersected_variant_id = self.variant_id if self.variant_id == other.variant_id and intersected_paradigm_id is not None else None
        intersected_form_tag = self.form_tag if self.form_tag == other.form_tag and intersected_paradigm_id is not None else None

        return ParadigmaFormId(intersected_paradigm_id, intersected_variant_id, intersected_form_tag) if intersected_paradigm_id is not None else None

    def union_with(self, other: Optional["ParadigmaFormId"]) -> "ParadigmaFormId":
        if other is None:
            return ParadigmaFormId.clone(self)

        return ParadigmaFormId(self.paradigm_id or other.paradigm_id, self.variant_id or other.variant_id, self.form_tag or other.form_tag)


TLinguisticTag = TypeVar("TLT", bound="LinguisticTag")


@dataclass
class LinguisticTag:
    """Усе вядомыя граматычныя тэгі аднаго слова"""

    PARSING_RE = re.compile(r"^\s*([\w.]*)(?:\|([\w.]*))?\s*$")

    def __init__(self, paradigm_tag: str, form_tag: str = None):
        self.paradigm_tag = paradigm_tag
        self.form_tag = form_tag

    paradigm_tag: str
    form_tag: str

    def pos(self) -> str | None:
        return self.paradigm_tag[0] if self.paradigm_tag and len(self.paradigm_tag) > 0 and self.paradigm_tag[0] != "." else None

    def __str__(self) -> str:
        return f"{self.paradigm_tag or ''}|{self.form_tag or ''}"

    def __repr__(self) -> str:
        return self.__str__()

    def intersect_with(self, other: Optional["LinguisticTag"]) -> Optional["LinguisticTag"]:
        if other is None:
            return None

        if not self.paradigm_tag or not other.paradigm_tag:
            intersected_paradigm_tag = None
        elif self.paradigm_tag[0] != other.paradigm_tag[0]:
            # калі гэта розныя часьціны мовы, ня будзем спрабаваць знайсьці нічога агульнага, хоць тэаарэтыыычна, штось магло б быць, але ну нафіг
            intersected_paradigm_tag = None
        else:
            intersected_paradigm_tag = LinguisticTag._intersect_strings(self.paradigm_tag, other.paradigm_tag)

        if not self.form_tag or not other.form_tag:
            intersected_form_tag = None
        else:
            intersected_form_tag = LinguisticTag._intersect_strings(self.form_tag, other.form_tag)

        if intersected_paradigm_tag is None and intersected_form_tag is None:
            return None

        return LinguisticTag(intersected_paradigm_tag, intersected_form_tag) if intersected_paradigm_tag is not None else None

    def union_with(self, other: Optional["LinguisticTag"]) -> "LinguisticTag":
        if other is None:
            return LinguisticTag.clone(self)

        if not self.paradigm_tag or not other.paradigm_tag:
            unioned_paradigm_tag = self.paradigm_tag or other.paradigm_tag
        elif self.paradigm_tag[0] != other.paradigm_tag[0]:
            # ні ідэі чаму б я аб'ядноўваў дзьве розныя часьціны мовы
            logger.warning(f"Злучэньне розных часьцінаў мовы {self} і {other}")
            unioned_paradigm_tag = self.paradigm_tag
        else:
            unioned_paradigm_tag = LinguisticTag._union_strings(self.paradigm_tag, other.paradigm_tag)

        if not self.form_tag or not other.form_tag:
            unioned_form_tag = self.form_tag or other.form_tag
        else:
            unioned_form_tag = LinguisticTag._union_strings(self.form_tag, other.form_tag)

        return LinguisticTag(unioned_paradigm_tag, unioned_form_tag)

    @staticmethod
    def clone(other: "LinguisticTag") -> "LinguisticTag":
        return LinguisticTag(other.paradigm_tag, other.form_tag)

    @staticmethod
    def from_string(string_repr: str) -> Optional["LinguisticTag"]:
        if not string_repr:
            return None

        match = LinguisticTag.PARSING_RE.match(string_repr)

        if not match:
            return None

        (paradigm_tag, form_tag) = match.groups()

        paradigm_tag = paradigm_tag or None
        form_tag = form_tag or None

        return LinguisticTag(paradigm_tag, form_tag)

    @staticmethod
    def _intersect_strings(str1, str2):
        max_len = max(len(str1), len(str2))
        str1 = str1.ljust(max_len)
        str2 = str2.ljust(max_len)

        return "".join(c1 if c1 == c2 else "." for c1, c2 in zip(str1, str2))

    @staticmethod
    def _union_strings(str1, str2):
        max_len = max(len(str1), len(str2))
        str1 = str1.ljust(max_len)
        str2 = str2.ljust(max_len)

        return "".join((c1 if c2 == "." else c2) or "." for c1, c2 in zip(str1, str2))


@dataclass
class LinguisticItem(SentenceItem):
    """Слова, ці іншы структурны элемэнт, з файлу verti, з усёю захаванаю пра яго інфармацыяй"""

    def __init__(self, text: str, type: SentenceItemType, glue_next=False):
        self.text = text
        self.type = type
        self.glue_next = glue_next

    paradigma_form_id: ParadigmaFormId
    lemma: str
    linguistic_tag: LinguisticTag
    comment: str
    metadata: object

    @staticmethod
    def from_sentence_item(sentence_item: SentenceItem):
        return LinguisticItem(sentence_item.text, sentence_item.type, sentence_item.glue_next)


@dataclass(frozen=True)
class GrammarInfo:
    """Клас для захоўвання граматычнай інфармацыі."""

    paradigma_form_id: ParadigmaFormId  # Ідэнтыфікатар парадыгмы і формы
    paradigm_line: int  # Нумар радка парадыгмы
    form_line: int  # Нумар радка формы
    linguistic_tag: LinguisticTag  # Граматычныя тэгі
    pos_id: str  # Літара часціны мовы
    pos: str  # Часціна мовы
    file_name: str  # Імя файла, дзе знаходзіцца парадыгма
    lemma: str  # Лема
    normalized_lemma: str  # Нормалізаваная лема
    meaning: str  # Значэнне
    properties: Dict[str, str]  # Граматычныя ўласцівасці
    form_description: List[str]  # Расшыфроўка граматычных пазнак
