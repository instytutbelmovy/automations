"""
Модуль для працы з граматычнай базай.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from lxml import etree


@dataclass
class GrammarInfo:
    """Клас для захоўвання граматычнай інфармацыі."""
    pos: str  # Частка мовы
    paradigm_tag: str  # Тэг парадыгмы
    lemma: str
    form_tag: str  # Тэг формы
    properties: Dict[str, str]  # Граматычныя ўласцівасці


class GrammarDB:
    """Клас для працы з граматычнай базай."""
    
    # Маппінг частак мовы
    POS_MAPPING = {
        'N': 'назоўнік',
        'A': 'прыметнік',
        'M': 'лічэбнік',
        'S': 'займеннік',
        'V': 'дзеяслоў',
        'P': 'дзеепрыметнік',
        'R': 'прыслоўе',
        'C': 'злучнік',
        'I': 'прыназоўнік',
        'E': 'часціца',
        'Y': 'выклічнік',
        'Z': 'пабочнае слова',
        'W': 'прэдыкатыў',
        'F': 'частка слова'
    }
    
    def __init__(self):
        self._word_forms: Dict[str, List[GrammarInfo]] = {}
        self._paradigms: Dict[str, Dict[str, str]] = {}
    
    def _normalize_form(self, form: str) -> str:
        """
        Нармалізацыя формы слова (выдаленне знака націску).
        
        Args:
            form: Форма слова
            
        Returns:
            Нармалізаваная форма
        """
        return form.replace('+', '')
    
    def load_from_xml(self, xml_path: Path) -> None:
        """
        Загрузка і індэксаванне граматычнай базы з XML файла.
        
        Args:
            xml_path: Шлях да XML файла
        """
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
        
        # Загружаем парадыгмы
        for paradigm in root.findall('.//Paradigm'):
            tag = paradigm.get('tag')
            if tag:
                self._paradigms[tag] = {}
                for prop in paradigm:
                    self._paradigms[tag][prop.tag] = prop.text
        
        # Загружаем словы
        for lemma_elem in root.findall('.//Lemma'):
            lemma = lemma_elem.text
            paradigm_elem = lemma_elem.getparent()
            paradigm_tag = paradigm_elem.get('tag')
            
            for form_elem in paradigm_elem.findall('.//Form'):
                form_tag = form_elem.get('tag')
                value = form_elem.text
                
                if value is not None:
                    # Нармалізуем форму для індэксавання
                    normalized_form = self._normalize_form(value)
                    
                    # Збіраем граматычныя ўласцівасці
                    properties = {}
                    for prop in form_elem:
                        properties[prop.tag] = prop.text
                    
                    grammar_info = GrammarInfo(
                        pos=self.POS_MAPPING.get(paradigm_tag[0], 'невядома'),
                        paradigm_tag=paradigm_tag,
                        lemma=lemma,
                        form_tag=form_tag,
                        properties=properties
                    )
                    
                    # Дадаем форму ў індэкс
                    if normalized_form not in self._word_forms:
                        self._word_forms[normalized_form] = []
                    self._word_forms[normalized_form].append(grammar_info)
    
    def load_directory(self, directory: Path) -> None:
        """
        Загрузка ўсіх XML файлаў з дырэкторыі.
        
        Args:
            directory: Шлях да дырэкторыі з XML файламі
        """
        for xml_file in directory.glob('*.xml'):
            self.load_from_xml(xml_file)
    
    def lookup_word(self, word: str) -> Optional[List[GrammarInfo]]:
        """
        Пошук слова ў базе.
        
        Args:
            word: Слова для пошуку
            
        Returns:
            Спіс магчымых граматычных варыянтаў або None, калі слова не знойдзена
        """
        normalized_word = self._normalize_form(word)
        return self._word_forms.get(normalized_word)
    
    def is_ambiguous(self, word: str) -> bool:
        """
        Праверка ці мае слова некалькі магчымых граматычных варыянтаў.
        
        Args:
            word: Слова для праверкі
            
        Returns:
            True калі ёсць некалькі варыянтаў, False калі адзін або няма
        """
        variants = self.lookup_word(word)
        return variants is not None and len(variants) > 1
    
    def get_paradigm_info(self, paradigm_tag: str) -> Optional[Dict[str, str]]:
        """
        Атрыманне інфармацыі пра парадыгму па яе тэгу.
        
        Args:
            paradigm_tag: Тэг парадыгмы
            
        Returns:
            Слоўнік з інфармацыяй пра парадыгму або None, калі парадыгма не знойдзена
        """
        return self._paradigms.get(paradigm_tag)
    
    def get_pos_variants(self, word: str) -> Set[str]:
        """
        Атрыманне ўсіх магчымых частак мовы для слова.
        
        Args:
            word: Слова для праверкі
            
        Returns:
            Мноства частак мовы
        """
        variants = self.lookup_word(word)
        if variants:
            return {v.pos for v in variants}
        return set()
    
    def get_all_forms(self, word: str) -> List[Tuple[str, str]]:
        """
        Атрыманне ўсіх формаў слова з іх тэгамі.
        
        Args:
            word: Слова для пошуку
            
        Returns:
            Спіс картэжаў (форма, тэг)
        """
        variants = self.lookup_word(word)
        if variants:
            return [(v.lemma, v.form_tag) for v in variants]
        return [] 