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
    paradigm_id: str  # ID парадыгмы
    variant_id: str  # ID варыянту
    paradigm_line: int  # Нумар радка парадыгмы
    form_line: int  # Нумар радка формы
    paradigm_tag: str  # Тэг парадыгмы
    pos: str  # Частка мовы
    form_tag: str  # Тэг формы
    file_name: str  # Імя файла, дзе знаходзіцца парадыгма
    variant_lemma: str  # Лема варыянта
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
    
    def _normalize_form(self, form: str) -> str:
        """
        Нармалізацыя формы слова (выдаленне знака націску, прывядзенне да ніжняга рэгістра,
        замена "ў" на "у" і "i" на "і").
        
        Args:
            form: Форма слова
            
        Returns:
            Нармалізаваная форма
        """
        # Прывядзенне да ніжняга рэгістра
        form = form.lower()
        # Замена літар
        form = form.replace('ў', 'у').replace('i', 'і')
        # Выдаленне знака націску
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
            paradigm_tag = paradigm.get('tag')
            paradigm_id = paradigm.get('pdgId')
            
            for variant in paradigm.findall('.//Variant'):
                variant_id = variant.get('id')
                variant_lemma = variant.get('lemma')
                variant_pravapis = variant.get('pravapis')
                variant_slouniki = variant.get('slouniki')
                variant_type = variant.get('type')
                variant_tag = variant.get('tag')  # Атрымліваем тэг варыянта
                
                # Выкарыстоўваем тэг варыянта, калі ён ёсць, інакш тэг парадыгмы
                effective_tag = variant_tag if variant_tag else paradigm_tag
                
                for form in variant.findall('.//Form'):
                    form_tag = form.get('tag')
                    form_slouniki = form.get('slouniki')
                    form_options = form.get('options')
                    form_value = form.text
                    
                    if form_value is not None:
                        # Нармалізуем форму для індэксавання
                        normalized_form = self._normalize_form(form_value)
                        
                        # Збіраем граматычныя ўласцівасці
                        properties = {
                            'variant_pravapis': variant_pravapis,
                            'variant_slouniki': variant_slouniki,
                            'form_slouniki': form_slouniki,
                            'form_options': form_options,
                            'variant_type': variant_type
                        }
                        
                        grammar_info = GrammarInfo(
                            paradigm_id=paradigm_id,
                            variant_id=variant_id,
                            paradigm_line=paradigm.sourceline,
                            form_line=form.sourceline,
                            paradigm_tag=effective_tag,
                            pos=self.POS_MAPPING.get(effective_tag[0], 'невядома'),
                            form_tag=form_tag,
                            file_name=xml_path.name,
                            variant_lemma=variant_lemma,
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
