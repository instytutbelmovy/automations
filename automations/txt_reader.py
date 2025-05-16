from pathlib import Path
from .doc_reader import DocReader, SourceDocument


class TxtReader(DocReader):
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
