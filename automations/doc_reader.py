from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


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


class DocReader(ABC):
    @abstractmethod
    def read(self, file_path: str | Path) -> SourceDocument:
        """Чытае дакумент па шляху і вяртае SourceDocument з метададзенымі і параграфамі."""
        pass
