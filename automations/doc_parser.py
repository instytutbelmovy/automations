from pathlib import Path
from typing import Type
from .doc_reader import DocReader, SourceDocument
from .tokenizer import Tokenizer
from .sentencer import Sentencer, SentenceItem
from .linguistic_bits import KorpusDocument, Paragraph, Sentence


class DocParser:
    def __init__(self, reader: Type[DocReader]):
        self.reader = reader()
        self.tokenizer = Tokenizer()
        self.sentencer = Sentencer()

    def parse(self, file_path: str | Path) -> KorpusDocument[SentenceItem]:
        """Чытае дакумент па шляху і вяртае KorpusDocument з метададзенымі і параграфамі."""
        source_doc = self.reader.read(file_path)

        document = KorpusDocument[SentenceItem](
            title=source_doc.title,
            author=source_doc.author,
            language=source_doc.language,
            publication_date=source_doc.publication_date,
        )

        # Апрацоўваем кожны параграф
        for paragraph in source_doc.paragraphs:
            # Токенізуем параграф
            tokens = self.tokenizer.parse(paragraph)
            # Разбіваем на сказы
            sentences = self.sentencer.to_sentences(tokens)
            # Ствараем аб'екты Sentence з SentenceItem
            sentence_objects = [Sentence(items=sentence) for sentence in sentences]
            # Дадаем параграф з сказамі
            document.paragraphs.append(Paragraph(sentences=sentence_objects))

        return document
