import re


class Normalizer:
    CORRECT_STRESS = "\u0301"
    GRAMMAR_DB_STRESS = "+"
    ALL_STRESSES = CORRECT_STRESS + "\u00b4"
    DB_STRESS_REPLACE_RE = re.compile(f"[{ALL_STRESSES}]")
    COMPLETELY_ALL_STRESSES = ALL_STRESSES + GRAMMAR_DB_STRESS  # creative name, huh?
    CORRECT_APOSTROPHE = "\u02bc"
    ALL_APOSTROPHES = CORRECT_APOSTROPHE + "'\u2019"
    DASH = "-"
    LETTERS = ALL_STRESSES + ALL_APOSTROPHES + DASH + "ёйцукенгґшўзхфывапролджэячсмітьъбющиЁЙЦУКЕНГҐШЎЗХФЫВАПРОЛДЖЭЯЧСМІТЬЪБЮЩИ" + "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM0123456789"

    def __init__(self):
        # Ініцыялізацыя табліц канвэртацыі
        self._tokinization_normalize = {}

        # Запаўненне базавых табліц
        for c in range(0x2020):
            if chr(c).isalnum():
                self._tokinization_normalize[chr(c)] = chr(c)

        # Апострафы
        for c in self.ALL_APOSTROPHES:
            self._tokinization_normalize[c] = self.CORRECT_APOSTROPHE

        # Націскі
        for c in self.ALL_STRESSES:
            self._tokinization_normalize[c] = self.CORRECT_STRESS

        # Ангельская i ў беларускую
        self._tokinization_normalize["i"] = "і"
        self._tokinization_normalize["I"] = "І"

        # Злучкі
        self._tokinization_normalize[self.DASH] = self.DASH

        self._lowercase_normalize = {key: value.lower() for key, value in self._tokinization_normalize.items()}
        self._grammar_search_aggressive_normalize = self._lowercase_normalize.copy()

        self._grammar_search_aggressive_normalize["ў"] = "у"
        self._grammar_search_aggressive_normalize["Ў"] = "у"

        self._grammar_search_light_normalize = self._tokinization_normalize.copy()
        self._grammar_search_light_normalize[self.GRAMMAR_DB_STRESS] = self.CORRECT_STRESS

    def tokinization_normalize(self, word: str) -> str:
        result = []
        for c in word:
            if normalized := self._tokinization_normalize.get(c):
                result.append(normalized)
        return "".join(result)

    def grammar_db_aggressive_normalize(self, word: str) -> str:
        result = []
        for c in word:
            if normalized := self._grammar_search_aggressive_normalize.get(c):
                result.append(normalized)
        return "".join(result)

    def grammar_db_light_normalize(self, word: str) -> str:
        result = []
        for c in word:
            if normalized := self._grammar_search_light_normalize.get(c):
                result.append(normalized)
        return "".join(result)

    def is_apostraf(self, c: str) -> bool:
        return c in self.ALL_APOSTROPHES

    def is_letter(self, c: str) -> bool:
        # todo а што рабіць зь неахайнымі выпадкамі калі замест націску хтось ужыў адразу камбінаваныя літары, кшталту áéó
        # прапанаванае вырашэньне - дадаць гэтыя літары ў LETTERS
        # а таксама дадаць маппінг у літару з камбінацыйным націскам
        return c in self.LETTERS

    def unstress(self, word: str) -> str:
        """Выдаляе ўсе знакі націску са слова."""
        return "".join(c for c in word if c not in self.COMPLETELY_ALL_STRESSES)

    def has_stress(self, word: str) -> bool:
        return any(c in self.COMPLETELY_ALL_STRESSES for c in word)

    def db_stress_normalize(self, word: str) -> str:
        return self.DB_STRESS_REPLACE_RE.sub(self.GRAMMAR_DB_STRESS, word)
