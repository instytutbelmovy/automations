import re
import logging
from typing import List, Tuple, Optional, Dict, TextIO, Iterator
from pathlib import Path
from grammar_db import GrammarDB
from anthropic_provider import AnthropicProvider, BaseProvider

class MorphologicalAnalyzer:

    POS_MAPPING = {
        'N': 'NOUN',
        'A': 'ADJ',
        'M': 'NUM',
        'S': 'PRON',
        'V': 'VERB',
        'P': 'ADJ',
        'R': 'ADV',
        'C': 'CCONJ',
        'I': 'ADP',
        'E': 'PART',
        'Y': 'INTJ',
        'Z': 'AUX',
        'W': 'AUX',
        'F': 'X'
    }

    def __init__(self, grammar_db: GrammarDB, provider: BaseProvider):
        """
        Ініцыялізацыя аналізатара
        
        Args:
            grammar_db: Гатовы аб'ект граматычнай базы даных
            provider: Аб'ект правайдэра для вырашэння аманіміі
        """
        self.grammar_db = grammar_db
        self.provider = provider
        self.logger = logging.getLogger(__name__)
        
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Разбіццё тэксту на сказы
        
        Args:
            text: Уваходны тэкст
            
        Returns:
            List[str]: Спіс сказаў
        """
        # Улічваем шматкроп'е і іншыя знакі прыпынку
        sentences = re.split(r'(?<=[.!?])\s+(?=[А-ЯІЎЁA-Z])|(?<=\.\.\.)\s+(?=[А-ЯІЎЁA-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def tokenize_sentence(self, sentence: str) -> List[str]:
        """
        Разбіццё сказа на словы
        
        Args:
            sentence: Сказ для разбіцця
            
        Returns:
            List[str]: Спіс слоў
        """
        # Улічваем асаблівасці беларускай мовы
        tokens = re.findall(r"[\w''\-]+|\.{3}|[.,!?;«—»:]", sentence)
        return [t for t in tokens if t.strip()]
    
    async def analyze_word(self, tokens: List[str], word_index: int) -> Optional[Tuple[str, str, str]]:
        """
        Аналіз слова з выкарыстаннем граматычнай базы
        
        Args:
            tokens: Спіс слоў у сказе
            word_index: Індэкс слова для аналізу
            
        Returns:
            Optional[Tuple[str, str, str]]: (слова, лема, часціна мовы) або None
        """
        if word_index < 0 or word_index >= len(tokens):
            return None
            
        word = tokens[word_index]
        
        # Апрацоўка знакаў прыпынку
        if re.match(r'^\.{3}|[.,!?;«—»:]$', word):
            return (word, word, 'PUNCT')
            
        # Пошук слова ў граматычнай базе
        variants = self.grammar_db.lookup_word(word)
        if not variants:
            return (word, None, None)
            
        if len(variants) == 1:
            grammar_info = variants[0]
            return (word, grammar_info.normalized_lemma, self.POS_MAPPING.get(grammar_info.pos_id, 'X'))
        else:
            context_tokens = tokens[:]
            context_tokens[word_index] = f"<word>{word}</word>"
            text_with_word = " ".join(context_tokens)
            
            self.logger.debug(text_with_word)
            probabilities = await self.provider.disambiguate(text_with_word, variants)
            for i, probability in enumerate(probabilities):
                info = variants[i]
                meaning_str = f" ({info.meaning})" if info.meaning else ""
                self.logger.debug(f"{probability:.2f}% {info.pos} \"{info.lemma.replace('+', '\u0301')}\"{meaning_str} {', '.join(info.form_description)}")
            
            # Выбіраем варыянт з найвышэйшай імавернасцю
            best_variant_index = probabilities.index(max(probabilities))
            best_variant = variants[best_variant_index]
            return (word, best_variant.normalized_lemma, self.POS_MAPPING.get(best_variant.pos_id, 'X'))
    
    async def process_stream(self, input_stream: TextIO, output_stream: TextIO, doc_id: str = "doc001", doc_index: int = 1) -> None:
        """
        Плыневая апрацоўка тэксту
        
        Args:
            input_stream: Уваходная плынь
            output_stream: Выходная плынь
            doc_id: Ідэнтыфікатар дакумента
            doc_index: Індэкс дакумента
        """
        output_stream.write(f'<doc file="{doc_id}" n="{doc_index}">\n')
        
        buffer = []
        for line in input_stream:
            line = line.rstrip('\n')
            if not line and buffer:  # Калі сустрэлі пусты радок і буфер не пусты
                await self._process_buffer(buffer, output_stream)
                buffer = []
            elif line:  # Калі радок не пусты
                buffer.append(line)
        
        if buffer:  # Апрацоўваем рэшту тэксту ў канцы плыні
            await self._process_buffer(buffer, output_stream)
            
        output_stream.write("</doc>\n")
        
    async def _process_buffer(self, buffer: List[str], output_stream: TextIO) -> None:
        """
        Апрацоўка буфера тэксту
        
        Args:
            buffer: Спіс радкоў тэксту
            output_stream: Выходная плынь
        """
        text = " ".join(buffer)
        sentences = self.split_into_sentences(text)
        
        for sentence in sentences:
            output_stream.write("<s>\n")
            tokens = self.tokenize_sentence(sentence)
            
            for i, token in enumerate(tokens):
                word, lemma, pos = await self.analyze_word(tokens, i)
                if (lemma is None):
                    output_stream.write(token + "\n")
                else:
                    output_stream.write(f"{token}\t{lemma}\t{pos}\n")
            
            output_stream.write("</s>\n") 