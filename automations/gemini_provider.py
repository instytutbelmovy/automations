"""
Правайдэр для выкарыстання Google Gemini API
"""

import logging
import os
import json
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel
from google import genai
from google.genai import types
from automations.base_provider import BaseProvider
from automations.grammar_db import GrammarInfo

class AnswerPair(BaseModel):
    number: int
    probability: int

class GeminiProvider(BaseProvider):
    """Правайдэр для выкарыстання Google Gemini API."""

    MAX_TOKENS = 400
    
    # Сістэмны промт
    SYSTEM_INSTRUCTION = """Ты лінгвіст, што спэцыялізуецца на беларускай мове. Твая задача — правесьці часцінамоўную і аманімічную клясыфікацыю вылучанага слова ў беларускім тэксьце.
Табе будзе прэзэнтаваны сказ і адно слова ў ім будзе вылучанае, таксама будуць прэзэнтаваныя варыянты парадыгм і часцін мовы якім можа адпавядаць гэтае слова.
Прааналізуй кантэкст, у якім сустракаецца вылучанае слова. Улічы ягоную граматычную ролю, навакольныя словы і агульны сэнс сказа.
Пасьля аналізу прызнач працэнт даверу кожнаму варыянту клясыфікацыі. Працэнты павінны адлюстроўваць тваю ступень упэўненасьці ў тым, што вылучанае слова адпавядае кожнай клясыфікацыі. Калі табе падаецца што патрэбная опцыя не прадстаўленая, то адсоткі могуць складаць менш чым 100% у суме.
Прэзэнтуй адказ у выглядзе адпаведных xml тэгаў з імавернасьцямі.
Вось некалькі прыкладаў.

<examples>
<example>
<!-- адсоткі могуць быць іншыя, ідэя ў тым што слушны варыянт 11 -->
<input>
{"text":"Ідзе гаворка без прымусы, Хвілінак першых <word>палі</word> путы,І душы насцеж разамкнуты.","options":[{"number":1,"description":"назоўнік \\"па́ля\\" родны склон, адзіночны лік"},{"number":2,"description":"назоўнік \\"па́ля\\" давальны склон, адзіночны лік"},{"number":3,"description":"назоўнік \\"па́ля\\" месны склон, адзіночны лік"},{"number":4,"description":"назоўнік \\"па́ля\\" назоўны склон, множны лік"},{"number":5,"description":"назоўнік \\"па́ля\\" вінавальны склон, множны лік"},{"number":6,"description":"назоўнік \\"по́ле\\" назоўны склон, множны лік"},{"number":7,"description":"назоўнік \\"по́ле\\" вінавальны склон, множны лік"},{"number":8,"description":"дзеяслоў \\"палі́ць\\" (спальваць) загадны лад, другая асоба, адзіночны лік"},{"number":9,"description":"дзеяслоў \\"палі́ць\\" (да ліць) загадны лад, другая асоба, адзіночны лік"},{"number":10,"description":"дзеяслоў \\"пало́ць\\" загадны лад, другая асоба, адзіночны лік"},{"number":11,"description":"дзеяслоў \\"па́сці\\" прошлы час, множны лік"}]}
</input>
<output>
[{"number":1,"probability":0},{"number":2,"probability":0},{"number":3,"probability":0},{"number":4,"probability":0},{"number":5,"probability":0},{"number":6,"probability":1},{"number":7,"probability":0},{"number":8,"probability":5},{"number":9,"probability":2},{"number":10,"probability":2},{"number":11,"probability":90}]
</output>
</example>
<example>
<input>
{"text":"Прайшлі <word>гады</word>, як мы не бачыліся.","options":[{"number":1,"description":"назоўнік \\"га́д\\" назоўны склон, множны лік"},{"number":2,"description":"назоўнік \\"го́д\\" назоўны склон, множны лік"},{"number":3,"description":"назоўнік \\"го́д\\" вінавальны склон, множны лік"}]}
</input>
<output>
[{"number":1,"probability":0},{"number":2,"probability":100},{"number":3,"probability":0}]
</output>
</example>
</examples>
"""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Ініцыялізацыя правайдэра.
        
        Args:
            model_name: Назва мадэлі Gemini
            api_key: API ключ (опцыянальна, можа быць узяты з GOOGLE_API_KEY)
        """
        self.model_name = model_name
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("API ключ ня знойдзены")
            
        self.client = genai.Client(api_key=api_key)
        self.logger = logging.getLogger(__name__)
        self._input_tokens = 0
        self._output_tokens = 0
        
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
        # Фарматуем опцыі ў JSON
        options = {
            "text": text,
            "options": [
                {"number": i+1, "description": self._format_grammar_option(variant)}
                for i, variant in enumerate(variants)
            ]
        }
        
        # Ствараем промт
        prompt = f"А вось уласна сказ для якога патрэбны аналіз:\n{json.dumps(options, ensure_ascii=False)}"
        
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=self.MAX_TOKENS,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=list[AnswerPair],
                system_instruction=self.SYSTEM_INSTRUCTION
            )
        )
        
        self._input_tokens += response.usage_metadata.prompt_token_count
        self._output_tokens += response.usage_metadata.candidates_token_count
        
        # Разбіраем JSON адказ
        probabilities = {}
        try:
            result = response.parsed
            for item in result:
                number = item.number
                probability = item.probability
                if number is not None:
                    probabilities[number] = probability
        except Exception as e:
            self.logger.error(f"Памылка разбору JSON: {e}")
            return [0.0] * len(variants)
            
        # Вяртаем спіс верагоднасьцяў у тым жа парадку
        return [probabilities.get(i + 1, 0.0) for i in range(len(variants))]

    
    def get_usage(self) -> Tuple[int, int, int]:
        """
        Атрымаць статыстыку выкарыстання токенаў.

        Returns:
            Tuple[int, int, int]: Выкарыстаныя токены ўводу, кэшу і вываду
        """
        return self._input_tokens, 0, self._output_tokens 