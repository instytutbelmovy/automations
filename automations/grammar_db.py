"""
Модуль для працы з граматычнай базай.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from lxml import etree
from functools import reduce
from .linguistic_bits import ParadigmaFormId, LinguisticTag, GrammarInfo
from .normalizer import Normalizer


class GrammarDB:
    """Клас для працы з граматычнай базай."""

    # Маппінг частак мовы
    POS_MAPPING = {
        "N": "назоўнік",
        "A": "прыметнік",
        "M": "лічэбнік",
        "S": "займеннік",
        "V": "дзеяслоў",
        "P": "дзеепрыметнік",
        "R": "прыслоўе",
        "C": "злучнік",
        "I": "прыназоўнік",
        "E": "часціца",
        "Y": "выклічнік",
        "Z": "пабочнае слова",
        "W": "прэдыкатыў",
        "F": "частка слова",
    }

    # Маппінг склонаў
    CASE_MAPPING = {
        "N": "назоўны склон",
        "G": "родны склон",
        "D": "давальны склон",
        "A": "вінавальны склон",
        "I": "творны склон",
        "L": "месны склон",
        "V": "клічны склон",
    }

    # Маппінг ліку
    NUMBER_MAPPING = {
        "S": "адзіночны лік",
        "P": "множны лік",
    }

    # Маппінг роду
    GENDER_MAPPING = {
        "M": "мужчынскі род",
        "F": "жаночы род",
        "N": "ніякі род",
        "P": "множны лік",
    }

    # Маппінг часу дзеяслова
    TENSE_MAPPING = {
        "R": "цяперашні час",
        "P": "прошлы час",
        "F": "будучы час",
    }

    # Маппінг асобы дзеяслова
    PERSON_MAPPING = {
        "1": "першая асоба",
        "2": "другая асоба",
        "3": "трэцяя асоба",
        "0": "безасабовая форма",
    }

    # Маппінг для займеннікаў (дадатковыя значэнні роду)
    PRONOUN_GENDER_MAPPING = {
        "M": "мужчынскі род",
        "F": "жаночы род",
        "N": "ніякі род",
        "0": "адсутнасць роду",
        "1": "адсутнасць форм",
    }

    # Маппінг ступеняў параўнання для прыслоўяў
    DEGREE_MAPPING = {
        "P": "станоўчая ступень",
        "C": "вышэйшая ступень",
        "S": "найвышэйшая ступень",
    }

    def __init__(self):
        self._word_forms: Dict[str, List[GrammarInfo]] = {}
        self._normalizer = Normalizer()

    def _decode_noun_form_tag(self, form_tag: str) -> List[str]:
        """
        Расшыфроўка граматычных пазнак для назоўнікаў.

        Args:
            form_tag: Тэг формы

        Returns:
            Спіс расшыфраваных пазнак
        """
        result = []

        if len(form_tag) == 2:  # Уласна назоўнікі
            # Першая літара - склон
            if form_tag[0] in self.CASE_MAPPING:
                result.append(self.CASE_MAPPING[form_tag[0]])
            # Другая літара - лік
            if form_tag[1] in self.NUMBER_MAPPING:
                result.append(self.NUMBER_MAPPING[form_tag[1]])

        elif len(form_tag) == 3:  # Субстантываваныя прыметнікі
            # Першая літара - род
            if form_tag[0] in self.GENDER_MAPPING:
                result.append(self.GENDER_MAPPING[form_tag[0]])
            # Другая літара - склон
            if form_tag[1] in self.CASE_MAPPING:
                result.append(self.CASE_MAPPING[form_tag[1]])
            # Трэцяя літара - лік
            if form_tag[2] in self.NUMBER_MAPPING:
                result.append(self.NUMBER_MAPPING[form_tag[2]])

        return result

    def _decode_adjective_form_tag(self, form_tag: str) -> List[str]:
        """
        Расшыфроўка граматычных пазнак для прыметнікаў.

        Args:
            form_tag: Тэг формы

        Returns:
            Спіс расшыфраваных пазнак
        """
        result = []

        if form_tag.startswith("R"):  # Прыметнік у функцыі прыслоўя
            result.append("у функцыі прыслоўя")
            return result

        if len(form_tag) == 3:  # Звычайны прыметнік
            # Першая літара - род
            if form_tag[0] in self.GENDER_MAPPING:
                result.append(self.GENDER_MAPPING[form_tag[0]])
            # Другая літара - склон
            if form_tag[1] in self.CASE_MAPPING:
                result.append(self.CASE_MAPPING[form_tag[1]])
            # Трэцяя літара - лік
            if form_tag[2] in self.NUMBER_MAPPING:
                result.append(self.NUMBER_MAPPING[form_tag[2]])

        return result

    def _decode_verb_form_tag(self, form_tag: str) -> List[str]:
        """
        Расшыфроўка граматычных пазнак для дзеясловаў.

        Args:
            form_tag: Тэг формы

        Returns:
            Спіс расшыфраваных пазнак
        """
        result = []

        if not form_tag:
            return result

        # Інфінітыў
        if form_tag == "0":
            result.append("інфінітыў")
            return result

        # Дзеепрыслоўе
        if len(form_tag) >= 2 and form_tag[1] == "G" and form_tag[0] in self.TENSE_MAPPING:
            result.append(self.TENSE_MAPPING[form_tag[0]])
            result.append("дзеепрыслоўе")
            return result

        # Загадны лад
        if form_tag.startswith("I"):
            result.append("загадны лад")
            if len(form_tag) >= 2:
                # Другая пазіцыя - асоба
                if form_tag[1] in self.PERSON_MAPPING:
                    result.append(self.PERSON_MAPPING[form_tag[1]])
                # Трэцяя пазіцыя - лік
                if len(form_tag) >= 3 and form_tag[2] in self.NUMBER_MAPPING:
                    result.append(self.NUMBER_MAPPING[form_tag[2]])
            return result

        # Абвесны лад
        if form_tag[0] in self.TENSE_MAPPING:  # Першая пазіцыя - час
            result.append(self.TENSE_MAPPING[form_tag[0]])

            if form_tag[0] == "P":  # Прошлы час
                if len(form_tag) >= 2:
                    # Другая пазіцыя - род
                    if form_tag[1] in self.GENDER_MAPPING:
                        result.append(self.GENDER_MAPPING[form_tag[1]])
                    # Трэцяя пазіцыя - лік
                    if len(form_tag) >= 3 and form_tag[2] in self.NUMBER_MAPPING:
                        result.append(self.NUMBER_MAPPING[form_tag[2]])
            else:  # Цяперашні або будучы час
                if len(form_tag) >= 2:
                    # Другая пазіцыя - асоба
                    if form_tag[1] in self.PERSON_MAPPING:
                        result.append(self.PERSON_MAPPING[form_tag[1]])
                    # Трэцяя пазіцыя - лік
                    if len(form_tag) >= 3 and form_tag[2] in self.NUMBER_MAPPING:
                        result.append(self.NUMBER_MAPPING[form_tag[2]])

        return result

    def _decode_participle_form_tag(self, form_tag: str) -> List[str]:
        """
        Расшыфроўка граматычных пазнак для дзеепрыметнікаў.

        Args:
            form_tag: Тэг формы

        Returns:
            Спіс расшыфраваных пазнак
        """
        result = []

        if not form_tag:
            return result

        if len(form_tag) >= 3:
            # Першая літара - род
            if form_tag[0] in self.GENDER_MAPPING:
                result.append(self.GENDER_MAPPING[form_tag[0]])

            # Другая літара - склон
            if form_tag[1] in self.CASE_MAPPING:
                result.append(self.CASE_MAPPING[form_tag[1]])

            # Трэцяя літара - лік
            if form_tag[2] in self.NUMBER_MAPPING:
                result.append(self.NUMBER_MAPPING[form_tag[2]])

        # Праверка на кароткую форму
        if form_tag.startswith("R"):
            result.append("кароткая форма")

        return result

    def _decode_numeral_form_tag(self, form_tag: str) -> List[str]:
        """
        Расшыфроўка граматычных пазнак для лічэбнікаў.

        Args:
            form_tag: Тэг формы

        Returns:
            Спіс расшыфраваных пазнак
        """
        result = []

        if not form_tag:
            return result

        # Праверка на нескланяльны лічэбнік
        if form_tag == "0":
            result.append("нескланяльны")
            return result

        if len(form_tag) >= 3:
            # Першая літара - род
            if form_tag[0] in self.GENDER_MAPPING:
                result.append(self.GENDER_MAPPING[form_tag[0]])

            # Другая літара - склон
            if form_tag[1] in self.CASE_MAPPING:
                result.append(self.CASE_MAPPING[form_tag[1]])

            # Трэцяя літара - лік
            if form_tag[2] in self.NUMBER_MAPPING:
                result.append(self.NUMBER_MAPPING[form_tag[2]])

        return result

    def _decode_pronoun_form_tag(self, form_tag: str) -> List[str]:
        """
        Расшыфроўка граматычных пазнак для займеннікаў.

        Args:
            form_tag: Тэг формы

        Returns:
            Спіс расшыфраваных пазнак
        """
        result = []

        if not form_tag:
            return result

        if len(form_tag) >= 3:
            # Першая літара - род
            if form_tag[0] in self.PRONOUN_GENDER_MAPPING:
                result.append(self.PRONOUN_GENDER_MAPPING[form_tag[0]])

            # Другая літара - склон
            if form_tag[1] in self.CASE_MAPPING:
                result.append(self.CASE_MAPPING[form_tag[1]])

            # Трэцяя літара - лік
            if form_tag[2] in self.NUMBER_MAPPING:
                result.append(self.NUMBER_MAPPING[form_tag[2]])

        return result

    def _decode_adverb_form_tag(self, form_tag: str) -> List[str]:
        """
        Расшыфроўка граматычных пазнак для прыслоўяў.

        Args:
            form_tag: Тэг формы

        Returns:
            Спіс расшыфраваных пазнак
        """
        result = []

        if not form_tag:
            return result

        # Ступень параўнання
        if form_tag in self.DEGREE_MAPPING:
            result.append(self.DEGREE_MAPPING[form_tag])

        return result

    def load_from_xml(self, xml_path: Path) -> None:
        """
        Загрузка і індэксаванне граматычнай базы з XML файла.

        Args:
            xml_path: Шлях да XML файла
        """
        tree = etree.parse(str(xml_path))
        root = tree.getroot()

        # Загружаем парадыгмы
        for paradigm in root.findall(".//Paradigm"):
            paradigm_tag = paradigm.get("tag")
            paradigm_id = paradigm.get("pdgId")
            paradigm_meaning = paradigm.get("meaning")

            for variant in paradigm.findall("./Variant"):
                variant_id = variant.get("id")
                lemma = variant.get("lemma")
                normalized_lemma = self._normalizer.grammar_db_light_normalize(lemma)
                variant_pravapis = variant.get("pravapis")
                variant_slouniki = variant.get("slouniki")
                variant_type = variant.get("type")
                variant_tag = variant.get("tag")

                effective_tag = variant_tag if variant_tag else paradigm_tag
                pos_id = effective_tag[0]

                for form in variant.findall("./Form"):
                    form_tag = form.get("tag")
                    form_slouniki = form.get("slouniki")
                    form_options = form.get("options")
                    form_value = form.text

                    if form_value is not None:
                        # Нармалізуем форму для індэксавання
                        normalized_form = self._normalizer.grammar_db_aggressive_normalize(form_value)

                        # Збіраем граматычныя ўласцівасці
                        properties = {
                            "variant_pravapis": variant_pravapis,
                            "variant_slouniki": variant_slouniki,
                            "form_slouniki": form_slouniki,
                            "form_options": form_options,
                            "variant_type": variant_type,
                        }

                        # Расшыфроўваем граматычныя пазнакі
                        form_description = []
                        if pos_id == "N" and form_tag:  # Калі гэта назоўнік
                            form_description = self._decode_noun_form_tag(form_tag)
                        elif pos_id == "A" and form_tag:  # Калі гэта прыметнік
                            form_description = self._decode_adjective_form_tag(form_tag)
                        elif pos_id == "V" and form_tag:  # Калі гэта дзеяслоў
                            form_description = self._decode_verb_form_tag(form_tag)
                        elif pos_id == "P" and form_tag:  # Калі гэта дзеепрыметнік
                            form_description = self._decode_participle_form_tag(form_tag)
                        elif pos_id == "M" and form_tag:  # Калі гэта лічэбнік
                            form_description = self._decode_numeral_form_tag(form_tag)
                        elif pos_id == "S" and form_tag:  # Калі гэта займеннік
                            form_description = self._decode_pronoun_form_tag(form_tag)
                        elif pos_id == "R" and form_tag:  # Калі гэта прыслоўе
                            form_description = self._decode_adverb_form_tag(form_tag)

                        grammar_info = GrammarInfo(
                            paradigma_form_id=ParadigmaFormId(int(paradigm_id), variant_id, form_tag),
                            paradigm_line=paradigm.sourceline,
                            form_line=form.sourceline,
                            linguistic_tag=LinguisticTag(effective_tag, form_tag),
                            pos_id=pos_id,
                            pos=self.POS_MAPPING.get(pos_id, "невядома"),
                            file_name=xml_path.name,
                            lemma=lemma,
                            normalized_lemma=normalized_lemma,
                            meaning=paradigm_meaning,
                            properties=properties,
                            form_description=form_description,
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
        for xml_file in directory.glob("*.xml"):
            self.load_from_xml(xml_file)

    def lookup_word(self, word: str) -> Optional[List[GrammarInfo]]:
        """
        Пошук слова ў базе.

        Args:
            word: Слова для пошуку

        Returns:
            Спіс магчымых граматычных варыянтаў або None, калі слова не знойдзена
        """
        normalized_word = self._normalizer.grammar_db_aggressive_normalize(word)
        return self._word_forms.get(normalized_word)

    def infer_grammar_info(self, word: str) -> Tuple[ParadigmaFormId, str, LinguisticTag]:
        """
        Выводзіць граматычную інфармацыю для слова.

        Args:
            word: Слова для аналізу

        Returns:
            ParadigmaFormId, лемма, LinguisticTag
        """
        grammar_info_list = self.lookup_word(word)
        if not grammar_info_list:
            return [None, None, None]

        # Калі знайшлі адназначнае супадзенне
        if len(grammar_info_list) == 1:
            grammar_info = grammar_info_list[0]
            return (
                grammar_info.paradigma_form_id,
                grammar_info.normalized_lemma,
                grammar_info.linguistic_tag,
            )

        paradigma_ids = map(lambda x: x.paradigma_form_id, grammar_info_list)
        intersection_paradigma_form_id = reduce(lambda acc, x: acc.intersect_with(x) if acc else None, paradigma_ids)

        linguistic_tag = map(lambda x: x.linguistic_tag, grammar_info_list)
        intersection_linguistic_tag = reduce(lambda acc, x: acc.intersect_with(x) if acc else None, linguistic_tag)

        # Правяраем, ці можа толькі аманімічныя леммы?
        lemmas = [self._normalizer.grammar_db_light_normalize(info.lemma) for info in grammar_info_list]
        intersection_lemma = lemmas[0] if len(set(lemmas)) == 1 else None

        if not intersection_lemma:
            # добра, а калі і націскі і вялікія літары праігнараваць?
            lemmas = [self._normalizer.grammar_db_aggressive_normalize(info.lemma) for info in grammar_info_list]
            intersection_lemma = lemmas[0] if len(set(lemmas)) == 1 else None

        # Калі знайшліся зусім розныя варыянты - вяртаем пустыя значэнні
        return (intersection_paradigma_form_id, intersection_lemma, intersection_linguistic_tag)
