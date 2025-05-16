from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import PyPDF2


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


class PdfReader:
    def __init__(self):
        pass

    def read(self, file_path: str | Path) -> SourceDocument:
        """Чытае PDF файл па шляху і вяртае SourceDocument з метададзенымі і параграфамі."""
        with open(str(file_path), "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)

            # Збіраем метададзеныя
            info = pdf_reader.metadata
            title = info.get("/Title", "Без назвы") if info else "Без назвы"
            author = info.get("/Author") if info else None
            # PDF звычайна не мае мовы і даты ў метададзеных

            document = SourceDocument(title=title, author=author, language=None, publication_date=None)

            # Апрацоўваем змесціва
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    # Разбіваем тэкст на параграфы
                    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
                    document.paragraphs.extend(paragraphs)

        return document
