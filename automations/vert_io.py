from .linguistic_bits import KorpusDocument, LinguisticItem, Sentence, Paragraph, SentenceItem, SentenceItemType, ParadigmaFormId, LinguisticTag, POS_MAPPING
from lxml import etree
import json
import re


class VertIO:
    WORD_SPLIT_RE = re.compile(r"[\t\n]")

    # Канстанты для тэгаў
    LINE_BREAK_TAG = "<lb/>"
    GLUE_TAG = "<g/>"
    PUNCT = "PUNCT"

    @staticmethod
    def write(document: KorpusDocument[LinguisticItem | SentenceItem], file_path: str) -> None:
        """
        Запісвае KorpusDocument у файл у нашым уласным прамежкавым фармаце verti.

        Args:
            document: KorpusDocument для запісу
            file_path: Шлях да файла для запісу

        Raises:
            ValueError: Калі сустракаецца невядомы тып элемента
        """
        with open(file_path, "w", encoding="utf-8") as f:
            # Запіс метададзеных. Крыху праз сраку, але лепей я не прыдумаў
            element = etree.Element("doc")
            if document.title:
                element.set("title", document.title)
            if document.author:
                element.set("author", document.author)
            if document.language:
                element.set("language", document.language)
            if document.publication_date:
                element.set("publication_date", document.publication_date)
            doc_element_string = etree.tostring(element, encoding="unicode")
            f.write(doc_element_string[:-2])  # Выдаляем зачыняючы тэг
            f.write(">\n")

            # Запіс параграфаў
            for paragraph in document.paragraphs:
                f.write("<p>\n")
                for sentence in paragraph.sentences:
                    f.write("<s>\n")
                    for item in sentence.items:
                        if item.type == SentenceItemType.Word:
                            # Запіс лінгвістычнай інфармацыі
                            f.write(f"{item.text}")
                            if isinstance(item, LinguisticItem):
                                metadata_json = json.dumps(item.metadata) if item.metadata else ""
                                comment_json = json.dumps(item.comment) if item.comment else ""
                                empty = ""  # bloody black makes " " out of ""
                                f.write(f"\t{item.paradigma_form_id or empty}\t{item.lemma or empty}\t{item.linguistic_tag or empty}\t{comment_json}\t{metadata_json}")
                            f.write("\n")
                            if item.glue_next:
                                f.write(f"{VertIO.GLUE_TAG}\n")
                        elif item.type == SentenceItemType.Punctuation:
                            # Запіс знака прыпынку
                            f.write(f"{item.text}\t{VertIO.PUNCT}\n")
                        elif item.type == SentenceItemType.LineBreak:
                            # Запіс пераходу на новы радок
                            f.write(f"{VertIO.LINE_BREAK_TAG}\n")
                        else:
                            raise ValueError(f"Невядомы тып элемента: {item.type}")
                    f.write("</s>\n")
                f.write("</p>\n")

            if document.title:
                f.write("</doc>\n")

    @staticmethod
    def write_vert(document: KorpusDocument[LinguisticItem], file_path: str) -> None:
        """
        Запісвае KorpusDocument у файл у фармаце vert.

        Args:
            document: KorpusDocument для запісу
            file_path: Шлях да файла для запісу

        Raises:
            ValueError: Калі сустракаецца невядомы тып элемента
        """
        with open(file_path, "w", encoding="utf-8") as f:
            # Запіс метададзеных. Крыху праз сраку, але лепей я не прыдумаў
            element = etree.Element("doc")
            if document.title:
                element.set("title", document.title)
            if document.author:
                element.set("author", document.author)
            if document.language:
                element.set("language", document.language)
            if document.publication_date:
                element.set("publication_date", document.publication_date)
            doc_element_string = etree.tostring(element, encoding="unicode")
            f.write(doc_element_string[:-2])  # Выдаляем зачыняючы тэг
            f.write(">\n")

            # Запіс параграфаў
            for paragraph in document.paragraphs:
                f.write("<p>\n")
                for sentence in paragraph.sentences:
                    f.write("<s>\n")
                    for item in sentence.items:
                        if item.type == SentenceItemType.Word:
                            # Запіс лінгвістычнай інфармацыі
                            f.write(f"{item.text}")
                            empty = ""  # bloody black makes " " out of ""
                            pos = item.linguistic_tag.pos() if item.linguistic_tag else None
                            f.write(f"\t{item.lemma or empty}\t{POS_MAPPING[pos] if pos else empty}")
                            f.write("\n")
                            if item.glue_next:
                                f.write(f"{VertIO.GLUE_TAG}\n")
                        elif item.type == SentenceItemType.Punctuation:
                            # Запіс знака прыпынку
                            f.write(f"{item.text}\t{item.text}\t{VertIO.PUNCT}\n")
                        elif item.type == SentenceItemType.LineBreak:
                            # Запіс пераходу на новы радок
                            f.write(f"{VertIO.LINE_BREAK_TAG}\n")
                        else:
                            raise ValueError(f"Невядомы тып элемента: {item.type}")
                    f.write("</s>\n")
                f.write("</p>\n")

            if document.title:
                f.write("</doc>\n")

    @staticmethod
    def read(file_path: str) -> KorpusDocument[LinguisticItem]:
        """
        Чытае KorpusDocument з файла ў фармаце vert.

        Args:
            file_path: Шлях да файла для чытання

        Returns:
            KorpusDocument з прачытанымі дадзенымі

        Raises:
            ValueError: Калі сустракаецца невядомая структура радка
        """
        document = KorpusDocument[LinguisticItem]("", None, None, None)
        current_paragraph = Paragraph[LinguisticItem]([])
        current_sentence = Sentence[LinguisticItem]([])

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                # Апрацоўка метададзеных
                if line.startswith("<doc"):
                    # Выцягванне метададзеных з тэга. Зноў-ткі, праз сраку крыху
                    close_index = line.rfind(">")
                    document_xml = etree.fromstring(line[:close_index] + "/>")
                    document.title = document_xml.get("title")
                    document.author = document_xml.get("author")
                    document.language = document_xml.get("language")
                    document.publication_date = document_xml.get("publication_date")

                # Апрацоўка параграфаў і сказаў
                elif line == "<p>\n":
                    current_paragraph = Paragraph[LinguisticItem]([])
                elif line == "</p>\n":
                    document.paragraphs.append(current_paragraph)
                elif line == "<s>\n":
                    current_sentence = Sentence[LinguisticItem]([])
                elif line == "</s>\n":
                    current_paragraph.sentences.append(current_sentence)
                elif line == f"{VertIO.LINE_BREAK_TAG}\n":
                    current_sentence.items.append(LinguisticItem(None, SentenceItemType.LineBreak))
                elif line == f"{VertIO.GLUE_TAG}\n":
                    current_sentence.items[-1].glue_next = True
                elif not line.startswith("</"):
                    # Апрацоўка элементаў сказа
                    parts = VertIO.WORD_SPLIT_RE.split(line)[:-1]

                    if len(parts) == 2 and parts[1] == VertIO.PUNCT:
                        # Знак прыпынку
                        current_sentence.items.append(LinguisticItem(parts[0], SentenceItemType.Punctuation))
                    else:
                        # Лінгвістычны элемент
                        text = parts[0]
                        paradigma_form_id_text = parts[1] if len(parts) > 1 else None
                        lemma = (parts[2] if len(parts) > 2 else None) or None
                        linguistic_tag = (parts[3] if len(parts) > 3 else None) or None
                        comment_text = parts[4] if len(parts) > 4 else None
                        if comment_text and (comment_text[0] == '"' and comment_text[-1] == '"' or comment_text[0] == "'" and comment_text[-1] == "'"):
                            comment = json.loads(comment_text)
                        else:
                            comment = comment_text
                        metadata = json.loads(parts[5]) if len(parts) > 5 and parts[5] else None

                        item = LinguisticItem(text, SentenceItemType.Word)
                        paradigma_form_id = ParadigmaFormId.from_string(paradigma_form_id_text)
                        item.paradigma_form_id = paradigma_form_id
                        item.lemma = lemma
                        item.linguistic_tag = LinguisticTag.from_string(linguistic_tag)
                        item.comment = comment
                        item.metadata = metadata
                        current_sentence.items.append(item)

        return document
