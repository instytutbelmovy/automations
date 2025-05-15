from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

"""
Дакумэнт прачытаны з txt файла. Зьмест прадстаўлены параграфамі што ёсьць проста тэкстам
"""


@dataclass
class SourceDocument:
    title: str
    author: Optional[str] = None
    language: Optional[str] = None
    publication_date: Optional[str] = None
    paragraphs: List[str] = None

    def __post_init__(self):
        if self.paragraphs is None:
            self.paragraphs = []


class TxtReader:
    def __init__(self):
        pass

    def read(self, file_path: str | Path) -> SourceDocument:
        """Чытае TXT файл па шляху і вяртае SourceDocument з метададзенымі і параграфамі."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Вызначаем назву з імя файла
        title = Path(file_path).stem

        document = SourceDocument(title=title)

        # Разбіваем на параграфы па пераносах радкоў
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        document.paragraphs = paragraphs

        return document
