from pathlib import Path
import PyPDF2
from .doc_reader import DocReader, SourceDocument


class PdfReader(DocReader):
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
