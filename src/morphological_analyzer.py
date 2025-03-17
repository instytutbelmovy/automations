import re
import os
import sys
import glob
import argparse
from typing import List, Tuple, Optional, Dict, TextIO, Iterator
from pathlib import Path
from grammar_db import GrammarDB

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

    def __init__(self, grammar_base_path: str):
        """
        Ініцыялізацыя аналізатара
        
        Args:
            grammar_base_path: Шлях да граматычнай базы
        """
        self.grammar_base_path = Path(grammar_base_path)
        self.grammar_db = GrammarDB()
        self.grammar_db.load_directory(self.grammar_base_path)
        
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
    
    def analyze_word(self, word: str) -> Optional[Tuple[str, str, str]]:
        """
        Аналіз слова з выкарыстаннем граматычнай базы
        
        Args:
            word: Слова для аналізу
            
        Returns:
            Optional[Tuple[str, str, str]]: (слова, лема, часціна мовы) або None
        """
        # Апрацоўка знакаў прыпынку
        if re.match(r'^\.{3}|[.,!?;«—»:]$', word):
            return (word, word, 'PUNCT')
            
        # Пошук слова ў граматычнай базе
        variants = self.grammar_db.lookup_word(word)
        if variants and len(variants) == 1:
            grammar_info = variants[0]
            return (word, grammar_info.normalized_lemma, self.POS_MAPPING.get(grammar_info.pos_id, 'X'))
        else:
            return (word, None, None)
    
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
            
            for token in tokens:
                word, lemma, pos = self.analyze_word(token)
                if (lemma is None):
                    output_stream.write(word + "\n")
                else:
                    output_stream.write(f"{word}\t{lemma}\t{pos}\n")
            
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
    parser = argparse.ArgumentParser(description='Марфалагічны аналізатар беларускага тэксту')
    parser.add_argument('-b', '--base', default='../grammar-base/',
                      help='Шлях да граматычнай базы (па змоўчанні: ../grammar-base/)')
    parser.add_argument('-i', '--input', nargs='*', default=[],
                      help='Шляхі да файлаў для апрацоўкі (падтрымліваецца globbing)')
    parser.add_argument('-o', '--output',
                      help='Шлях для захавання выніку. Калі зададзены некалькі ўваходных файлаў, можа быць тэчкай')
    
    args = parser.parse_args()
    
    analyzer = MorphologicalAnalyzer(args.base)
    
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
            process_file(analyzer, input_file, args.output)

if __name__ == "__main__":
    main() 