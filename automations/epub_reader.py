from dataclasses import dataclass
from typing import List, Optional
from ebooklib import epub
from ebooklib.epub import EpubBook, EpubHtml
from pathlib import Path

'''
Дакумэнт прачытаны з epub (ці можа іншай крыніцы). Зьмест прадстаўлены параграфамі што ёсьць проста тэкстам
'''
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

class EpubReader:
    def __init__(self):
        pass

    def read(self, file_path: str | Path) -> SourceDocument:
        """Чытае EPUB файл па шляху і вяртае SourceDocument з метададзенымі і параграфамі."""
        book = epub.read_epub(str(file_path), options={'ignore_ncx': True}) # epub бібліятэка штось выдавала варнінг пра гэты ignore_ncx, то я вось і ягоны выбар яўным.
        
        # Збіраем метададзеныя
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else "Без назвы"
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else None
        language = book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else None
        date = book.get_metadata('DC', 'date')[0][0] if book.get_metadata('DC', 'date') else None

        document = SourceDocument(
            title=title,
            author=author,
            language=language,
            publication_date=date
        )

        # Апрацоўваем змесціва
        for item in book.get_items():
            if isinstance(item, EpubHtml):
                paragraphs = self._extract_paragraphs(item.get_content().decode('utf-8'))
                document.paragraphs.extend(paragraphs)

        return document

    def _is_poetry_block(self, element) -> bool:
        """Правярае, ці з'яўляецца элемент блокам паэзіі."""
        if element.get('class') == ['POETRY']:
            return True
        if element.find('div', class_='POETRY'):
            return True
        return False

    def _is_inside_poetry(self, element) -> bool:
        """Правярае, ці знаходзіцца элемент унутры блока паэзіі."""
        return element.find_parent('div', class_='POETRY') is not None

    def _extract_paragraphs(self, html_content: str) -> List[str]:
        """Вылучае параграфы з HTML змесціва."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        paragraphs = []

        # Спачатку збіраем усе элементы
        elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'])
        
        i = 0
        while i < len(elements):
            element = elements[i]
            
            # Правяраем, ці з'яўляецца блок паэзіяй
            if self._is_poetry_block(element):
                # Збіраем усе радкі паэзіі ў адзін параграф
                poetry_lines = []
                # Праходзім па ўсіх наступных элементах, пакуль не сустрэнем не-паэзію
                while i < len(elements) and self._is_poetry_block(elements[i]):
                    # Збіраем усе параграфы ўнутры блока паэзіі
                    for p in elements[i].find_all('p'):
                        text = p.get_text().strip()
                        if text:
                            poetry_lines.append(text)
                    i += 1
                if poetry_lines:
                    paragraphs.append('\n'.join(poetry_lines))
                continue
            
            # Пропускаем параграфы ўнутры паэзіі
            if element.name == 'p' and self._is_inside_poetry(element):
                i += 1
                continue
            
            # Звычайныя параграфы
            text = element.get_text().strip()
            if text and not element.get('class') == ['CLEAR']:  # Пропускаем пустыя элементы
                paragraphs.append(text)
            i += 1

        return paragraphs 