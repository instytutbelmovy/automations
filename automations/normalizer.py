class Normalizer:
    PRAVILNY_NACISK = '\u0301'
    USIE_NACISKI = PRAVILNY_NACISK + "\u00B4"
    PRAVILNY_APOSTRAF = '\u02BC'
    USIE_APOSTRAFY = PRAVILNY_APOSTRAF + "\'\u2019"
    DASH = '-'
    LETTERS = (USIE_NACISKI + USIE_APOSTRAFY + DASH +
                       "ёйцукенгшўзхфывапролджэячсмітьъбющиЁЙЦУКЕНГШЎЗХФЫВАПРОЛДЖЭЯЧСМІТЬЪБЮЩИ" +
                       "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM0123456789")
    
    def __init__(self):
        
        # Ініцыялізацыя табліц канвэртацыі
        self._znak_normalize = {}
        self._lowercase_normalize = {}
        self._super_normalize = {}
        
        # Запаўненне базавых табліц
        for c in range(0x2020):
            if chr(c).isalnum():
                self._znak_normalize[chr(c)] = chr(c)
                self._lowercase_normalize[chr(c)] = chr(c).lower()
        
        # Апострафы
        for c in self.USIE_APOSTRAFY:
            self._znak_normalize[c] = self.PRAVILNY_APOSTRAF
            self._lowercase_normalize[c] = self.PRAVILNY_APOSTRAF
        
        # Злучкі
        self._znak_normalize[self.DASH] = self.DASH
        self._lowercase_normalize[self.DASH] = self.DASH

        # Канвертацыя ґ -> г
        self._lowercase_normalize['ґ'] = 'г'
        self._lowercase_normalize['Ґ'] = 'г'
        
        # Ініцыялізацыя супэр-нармалізацыі
        self._super_normalize = self._lowercase_normalize.copy()
        
        # Дадатковая канвэртацыя мяккіх у цьвёрдыя
        conversions = {
            'ґ': 'г', 'ў': 'у', 'й': 'і', 'ё': 'о',
            'е': 'э', 'я': 'а', 'ю': 'у', 'ь': '', 'i': 'і'
        }
        
        for key, value in conversions.items():
            self._super_normalize[key] = value
            self._super_normalize[key.upper()] = value


#    def hash(self, word: str) -> int:
#        if not word:
#            return 0
#        result = 0
#        for c in word:
#            normalized = self._super_normalize.get(c, '')
#            if normalized:
#                result = 31 * result + ord(normalized)
#        return result
    
    def znak_normalized(self, word: str, preserve_chars: str = '') -> str:
        result = []
        for c in word:
            if c in preserve_chars:
                result.append(c)
                continue
            normalized = self._znak_normalize.get(c, '')
            if normalized:
                result.append(normalized)
        return ''.join(result)

    def is_apostraf(self, c: str) -> bool:
        return c in self.USIE_APOSTRAFY

    def is_letter(self, c: str) -> bool:
        return c in self.LETTERS 

#    def light_normalized(self, word: str, preserve_chars: str = '') -> str:
#        result = []
#        for i, c in enumerate(word):
#            if c in preserve_chars:
#                result.append(c)
#                continue
#            normalized = self._lowercase_normalize.get(c, '')
#            if normalized:
#                if i == 0:
#                    if normalized == 'ў':
#                        normalized = 'у'
#                    elif normalized == 'й':
#                        normalized = 'і'
#                result.append(normalized)
#        return ''.join(result)
#    
#    def super_normalized(self, word: str, preserve_chars: str = '') -> str:
#        result = []
#        for c in word:
#            if c in preserve_chars:
#                result.append(c)
#                continue
#            if c in ('щ', 'Щ'):
#                result.append('шч')
#                continue
#            if c in ('и', 'И'):
#                result.append('і')
#                continue
#            normalized = self._super_normalize.get(c, '')
#            if normalized:
#                result.append(normalized)
#        return ''.join(result)