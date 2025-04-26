"""
Правайдэр для выкарыстання Anthropic API
"""

import logging
import os
import re
from typing import List, Dict, Optional, Tuple
import anthropic
from .base_provider import BaseProvider
from .linguistic_bits import GrammarInfo

class AnthropicProvider(BaseProvider):
    """Правайдэр для выкарыстання Anthropic API."""

    MAX_TOKENS = 400
    
    # Сістэмны промт
    SYSTEM_MESSAGES = [
        {
            "type": "text",
            "text": "Ты лінгвіст, што спэцыялізуецца на беларускай мове. Твая задача — правесьці часцінамоўную і аманімічную клясыфікацыю вылучанага слова ў беларускім тэксьце.\n"
        },
        {
            "type": "text",
            "text": """Табе будзе прэзэнтаваны сказ і адно слова ў ім будзе вылучанае, таксама будуць прэзэнтаваныя варыянты парадыгм і часцін мовы якім можа адпавядаць гэтае слова.
Прааналізуй кантэкст, у якім сустракаецца вылучанае слова. Улічы ягоную граматычную ролю, навакольныя словы і агульны сэнс сказа.
Пасьля аналізу прызнач працэнт даверу кожнаму варыянту клясыфікацыі. Працэнты павінны адлюстроўваць тваю ступень упэўненасьці ў тым, што вылучанае слова адпавядае кожнай клясыфікацыі. Калі табе падаецца што патрэбная опцыя не прадстаўленая, то адсоткі могуць складаць менш чым 100% у суме.
Прэзэнтуй адказ у выглядзе адпаведных xml тэгаў з імавернасьцямі.
Вось некалькі прыкладаў.

<examples>
<example>
<example_description>
адсоткі могуць быць іншыя, ідэя ў тым што слушны варыянт 11
</example_description>
<text>
Ідзе гаворка без прымусы, Хвілінак першых <word>палі</word> путы, І душы насцеж разамкнуты.
</text>
<options>
<option number="1">назоўнік "па́ля" родны склон, адзіночны лік</option>
<option number="2">назоўнік "па́ля" давальны склон, адзіночны лік</option>
<option number="3">назоўнік "па́ля" месны склон, адзіночны лік</option>
<option number="4">назоўнік "па́ля" назоўны склон, множны лік</option>
<option number="5">назоўнік "па́ля" вінавальны склон, множны лік</option>
<option number="6">назоўнік "по́ле" назоўны склон, множны лік</option>
<option number="7">назоўнік "по́ле" вінавальны склон, множны лік</option>
<option number="8">дзеяслоў "палі́ць" (спальваць) загадны лад, другая асоба, адзіночны лік</option>
<option number="9">дзеяслоў "палі́ць" (да ліць) загадны лад, другая асоба, адзіночны лік</option>
<option number="10">дзеяслоў "пало́ць" загадны лад, другая асоба, адзіночны лік</option>
<option number="11">дзеяслоў "па́сці" прошлы час, множны лік</option>
</options>
<output>
<option number="1">0</option>
<option number="2">0</option>
<option number="3">0</option>
<option number="4">0</option>
<option number="5">0</option>
<option number="6">1</option>
<option number="7">0</option>
<option number="8">5</option>
<option number="9">2</option>
<option number="10">2</option>
<option number="11">90</option>
</output>
</example>
<example>
<text>
Прайшлі <word>гады</word>, як мы не бачыліся.
</text>
<options>
<option number="1">назоўнік "га́д" назоўны склон, множны лік</option>
<option number="2">назоўнік "го́д" назоўны склон, множны лік</option>
<option number="3">назоўнік "го́д" вінавальны склон, множны лік</option>
</options>
<output>
<option number="1">0</option>
<option number="2">100</option>
<option number="3">0</option>
</output>
</example>
</examples>""",
            "cache_control": {"type": "ephemeral"}
        }
    ]

    OUTPUT_PREFIX = "<option number=\"1\">"
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Ініцыялізацыя правайдэра.
        
        Args:
            model_name: Назва мадэлі Anthropic
            api_key: API ключ (опцыянальна, можа быць узяты з ANTHROPIC_API_KEY)
        """
        self.model_name = model_name
        api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API ключ ня знойдзены")
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key
        )
        self.logger = logging.getLogger(__name__)
        self._input_tokens = 0
        self._cache_tokens = 0
        self._output_tokens = 0
        
    async def _api_call(self, prompt: str) -> str:
        """
        API запыт да Anthropic.
        
        Args:
            prompt: Карыстальніцкі промт
            
        Returns:
            Адказ ад мадэлі
        """
        message = await self.client.messages.create(
            model=self.model_name,
            max_tokens=self.MAX_TOKENS,
            system=self.SYSTEM_MESSAGES,
            messages=[
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": self.OUTPUT_PREFIX}
            ]
        )
        self._input_tokens += message.usage.input_tokens + message.usage.cache_creation_input_tokens
        self._cache_tokens += message.usage.cache_read_input_tokens
        self._output_tokens += message.usage.output_tokens

        return message.content[0].text
        
    def _parse_output(self, output: str) -> Dict[int, float]:
        """
        Разбор выніку ад мадэлі з дапамогай рэгулярных выразаў.
        
        Args:
            output: Тэкст з адказам, які змяшчае <option> тэгі
            
        Returns:
            Слоўнік {нумар опцыі: імавернасць}
        """
        output = self.OUTPUT_PREFIX + output
        result = {}
        
        # Шукаем усе пары нумар-імавернасць
        pattern = r'<option\s+number="(\d+)">(\d+(?:\.\d+)?)%?</option>'
        matches = re.finditer(pattern, output)
        
        for match in matches:
            try:
                number = int(match.group(1))
                probability = float(match.group(2))
                result[number] = probability
            except (ValueError, IndexError):
                continue
                
        return result

        
    def _format_grammar_option(self, info: GrammarInfo) -> str:
        """
        Фарматаванне граматычнай інфармацыі ў чытэльны выгляд.
        
        Args:
            info: Граматычная інфармацыя
            
        Returns:
            Адфарматаваны тэкст
        """
        
        meaning_str = f" ({info.meaning})" if info.meaning else ""
        return f"{info.pos} \"{info.lemma.replace('+', '\u0301')}\"{meaning_str} {', '.join(info.form_description)}"
        
    async def disambiguate(self, text: str, variants: List[GrammarInfo]) -> List[float]:
        """
        Вырашэнне аманіміі для слова ў тэксце.
        
        Args:
            text: Поўны тэкст сказа з вылучаным словам у фармаце <word>слова</word>
            variants: Спіс магчымых граматычных варыянтаў
            
        Returns:
            Спіс верагоднасьцяў для кожнага варыянту ў тым жа парадку, што і ўваходны спіс variants
        """
        # Фарматуем опцыі ў XML
        options_xml = "\n".join(
            f'<option number="{i+1}">{self._format_grammar_option(variant)}</option>'
            for i, variant in enumerate(variants)
        )
        
        # Ствараем промт
        user_prompt = f"""
А вось уласна сказ для якога патрэбны аналіз:
<text>
{text}
</text>
<options>
{options_xml}
</options>
"""
        
        # Выклікаем API
        response = await self._api_call(user_prompt)
        
        # Разбіраем вынік
        probabilities = self._parse_output(response)
        
        # Вяртаем спіс верагоднасьцяў у тым жа парадку, што і ўваходны спіс variants
        return [probabilities.get(i + 1, 0.0) for i in range(len(variants))] 
    
    def get_usage(self) -> Tuple[int, int, int]:
        return self._input_tokens, self._cache_tokens, self._output_tokens
