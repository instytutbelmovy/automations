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
            if document.n:
                element.set("n", str(document.n))
            if document.title:
                element.set("title", document.title)
            if document.author:
                element.set("author", document.author)
            if document.language:
                element.set("language", document.language)
            if document.publication_date:
                element.set("publication_date", document.publication_date)
            if document.url:
                element.set("url", document.url)
            if document.type:
                element.set("type", document.type)
            if document.style:
                element.set("style", document.style)
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
                    document.n = document_xml.get("n")
                    document.title = document_xml.get("title")
                    document.author = document_xml.get("author")
                    document.language = document_xml.get("language")
                    document.publication_date = document_xml.get("publication_date")
                    document.url = document_xml.get("url")
                    document.type = document_xml.get("type")
                    document.style = document_xml.get("style")

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

    @staticmethod
    def read_doc_header(file_path: str) -> KorpusDocument:
        """
        Чытае толькі загаловак дакумента з verti/vert файла.

        Args:
            file_path: Шлях да файла

        Returns:
            KorpusDocument з прачытанымі мэтаданымі
        """
        document = KorpusDocument()

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("<doc"):
                    # Выцягванне мэтададзеных з тэга
                    close_index = line.rfind(">")
                    document_xml = etree.fromstring(line[:close_index] + "/>")
                    document.n = document_xml.get("n")
                    document.title = document_xml.get("title")
                    document.author = document_xml.get("author")
                    document.language = document_xml.get("language")
                    document.publication_date = document_xml.get("publication_date")
                    document.url = document_xml.get("url")
                    document.type = document_xml.get("type")
                    document.style = document_xml.get("style")
                    break
                elif not line.startswith("<!--"):  # Ігнараванне каментароў. Ня ведаю, для чаго, там іх і не павінна быць
                    break

        return document

    @staticmethod
    def update_doc_header(file_path: str, document: KorpusDocument, overwrite: bool = False) -> None:
        """
        Абнаўляе загаловак дакумента ў verti/vert файле.

        Args:
            file_path: Шлях да файла
            document: KorpusDocument з новымі мэтаданымі
            overwrite: Ці перазапісваць існуючыя мэтаданыя
        """
        # Чытаем існуючыя мэтаданыя
        existing_doc = VertIO.read_doc_header(file_path)

        existing_doc.n = document.n if not existing_doc.n or overwrite else existing_doc.n
        existing_doc.title = document.title if not existing_doc.title or overwrite else existing_doc.title
        existing_doc.author = document.author if not existing_doc.author or overwrite else existing_doc.author
        existing_doc.language = document.language if not existing_doc.language or overwrite else existing_doc.language
        existing_doc.publication_date = document.publication_date if not existing_doc.publication_date or overwrite else existing_doc.publication_date
        existing_doc.url = document.url if not existing_doc.url or overwrite else existing_doc.url
        existing_doc.type = document.type if not existing_doc.type or overwrite else existing_doc.type
        existing_doc.style = document.style if not existing_doc.style or overwrite else existing_doc.style

        # Ствараем новы загаловак
        element = etree.Element("doc")
        if existing_doc.n:
            element.set("n", str(existing_doc.n))
        if existing_doc.title:
            element.set("title", existing_doc.title)
        if existing_doc.author:
            element.set("author", existing_doc.author)
        if existing_doc.language:
            element.set("language", existing_doc.language)
        if existing_doc.publication_date:
            element.set("publication_date", existing_doc.publication_date)
        if existing_doc.url:
            element.set("url", existing_doc.url)
        if existing_doc.type:
            element.set("type", existing_doc.type)
        if existing_doc.style:
            element.set("style", existing_doc.style)

        new_header = etree.tostring(element, encoding="unicode")[:-2] + ">\n"

        # Чытаем файл па радках і замяняем загаловак
        with open(file_path, "r", encoding="utf-8") as f:
            lines = []
            header_found = False
            for line in f:
                if not header_found and line.startswith("<doc"):
                    lines.append(new_header)
                    header_found = True
                else:
                    lines.append(line)

        # Запісваем зменены файл
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
