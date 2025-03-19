import re
import os
import sys
import glob
import logging
import argparse
from dotenv import load_dotenv
from typing import List, Tuple, Optional, Dict, TextIO, Iterator
from pathlib import Path
from setup_logging import setup_logging
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
    
    def analyze_word(self, tokens: List[str], word_index: int) -> Optional[Tuple[str, str, str]]:
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
            
            self.logger.debug(f"?{text_with_word}")
            probabilities = self.provider.disambiguate(text_with_word, variants)
            for i, probability in enumerate(probabilities):
                info = variants[i]
                meaning_str = f" ({info.meaning})" if info.meaning else ""
                self.logger.debug(f"{probability:.2f}% {info.pos} \"{info.lemma.replace('+', '\u0301')}\"{meaning_str} {', '.join(info.form_description)}")
            
            # Выбіраем варыянт з найвышэйшай імавернасцю
            best_variant_index = probabilities.index(max(probabilities))
            best_variant = variants[best_variant_index]
            return (word, best_variant.normalized_lemma, self.POS_MAPPING.get(best_variant.pos_id, 'X'))
    
    def process_stream(self, input_stream: TextIO, output_stream: TextIO, doc_id: str = "doc001", doc_index: int = 1) -> None:
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
                self._process_buffer(buffer, output_stream)
                buffer = []
            elif line:  # Калі радок не пусты
                buffer.append(line)
        
        if buffer:  # Апрацоўваем рэшту тэксту ў канцы плыні
            self._process_buffer(buffer, output_stream)
            
        output_stream.write("</doc>\n")
        
    def _process_buffer(self, buffer: List[str], output_stream: TextIO) -> None:
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
                word, lemma, pos = self.analyze_word(tokens, i)
                if (lemma is None):
                    output_stream.write(token + "\n")
                else:
                    output_stream.write(f"{token}\t{lemma}\t{pos}\n")
            
            output_stream.write("</s>\n")

def process_file(analyzer: MorphologicalAnalyzer, input_path: str, output_path: Optional[str] = None) -> None:
    """
    Апрацоўка аднаго файла
    
    Args:
        analyzer: Экзэмпляр аналізатара
        input_path: Шлях да ўваходнага файла
        output_path: Шлях да выходнага файла ці тэчкі (опцыянальна)
    """
    input_path = Path(input_path)
    
    if output_path is None:
        output_file = str(input_path.with_suffix('.vert'))
    else:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_file = str(output_path / input_path.with_suffix('.vert').name)
        else:
            output_file = str(output_path)
            
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
    with open(input_path, 'r', encoding='utf-8') as input_file:
        with open(output_file, 'w', encoding='utf-8') as output_file:
            doc_id = input_path.stem
            analyzer.process_stream(input_file, output_file, doc_id)

def main():
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO")

    parser = argparse.ArgumentParser(description='Марфалагічны аналізатар беларускага тэксту')
    parser.add_argument('-b', '--base', default='../grammar-base/',
                      help='Шлях да граматычнай базы (па змоўчанні: ../grammar-base/)')
    parser.add_argument('-i', '--input', nargs='*', default=[],
                      help='Шляхі да файлаў для апрацоўкі (падтрымліваецца globbing)')
    parser.add_argument('-o', '--output',
                      help='Шлях для захавання выніку. Калі зададзены некалькі ўваходных файлаў, можа быць тэчкай')
    parser.add_argument('-m', '--model', default='claude-3-7-sonnet-20250219',
                      help='Назва мадэлі Anthropic для вырашэння аманіміі')
    parser.add_argument('--log-level', default=log_level,
                      help='Узровень лагавання (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    
    args = parser.parse_args()


    setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    # Ствараем неабходныя аб'екты
    provider = AnthropicProvider(args.model)
    logger.info(f"Індэксацыя граматычнай базы...")
    grammar_db = GrammarDB()
    grammar_db.load_directory(Path(args.base))
    logger.info(f"Індэксацыя граматычнай базы выканана")
    
    # Ініцыялізуем аналізатар
    analyzer = MorphologicalAnalyzer(grammar_db, provider)
    
    if not args.input:  # Калі няма ўваходных файлаў, працуем з stdin/stdout
        analyzer.process_stream(sys.stdin, sys.stdout)
    else:
        input_files = []
        for pattern in args.input:
            matched_files = glob.glob(pattern)
            if not matched_files:
                print(f"Папярэджанне: па шаблону '{pattern}' файлаў не знойдзена",
                      file=sys.stderr)
            input_files.extend(matched_files)
            
        if not input_files:
            print("Памылка: не знойдзена файлаў для апрацоўкі", file=sys.stderr)
            sys.exit(1)
            
        if args.output and not os.path.isdir(args.output) and len(input_files) > 1:
            print(f"Памылка: '{args.output}' павінна быць тэчкай пры апрацоўцы некалькіх файлаў",
                  file=sys.stderr)
            sys.exit(1)
            
        for input_file in input_files:
            logger.info(f"Апрацоўка файла: {input_file}")
            process_file(analyzer, input_file, args.output)

    input_tokens, cache_tokens, output_tokens = provider.get_usage()
    logger.info(f"Выкарыстана {input_tokens} вводу, {cache_tokens} кэшу, {output_tokens} вываду")

if __name__ == "__main__":
    main() 