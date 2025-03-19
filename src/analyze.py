import os
import sys
import glob
import logging
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from morphological_analyzer import MorphologicalAnalyzer
from grammar_db import GrammarDB
from anthropic_provider import AnthropicProvider
from gemini_provider import GeminiProvider
from setup_logging import setup_logging

async def process_file(analyzer: MorphologicalAnalyzer, input_path: str, output_path: str | None = None) -> None:
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
            await analyzer.process_stream(input_file, output_file, doc_id)

async def main():
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO")

    parser = argparse.ArgumentParser(description='Марфалагічны аналізатар беларускага тэксту')
    parser.add_argument('-b', '--base', default='../grammar-base/',
                      help='Шлях да граматычнай базы (па змоўчанні: ../grammar-base/)')
    parser.add_argument('-i', '--input', nargs='*', default=[],
                      help='Шляхі да файлаў для апрацоўкі (падтрымліваецца globbing)')
    parser.add_argument('-o', '--output',
                      help='Шлях для захавання выніку. Калі зададзены некалькі ўваходных файлаў, можа быць тэчкай')
    parser.add_argument('--log-level', default=log_level,
                      help='Узровень лагавання (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    
    args = parser.parse_args()

    setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    # Ствараем неабходныя аб'екты
    provider_type = os.getenv("PROVIDER_TYPE", "gemini")
    if provider_type == "anthropic":
        model = 'claude-3-7-sonnet-20250219'
        provider = AnthropicProvider(model)
    else:
        model = 'gemini-2.0-flash'
        provider = GeminiProvider(model)
    
    logger.info(f"Выкарыстоўваем мадэль {model}")
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
            await process_file(analyzer, input_file, args.output)

    input_tokens, cache_tokens, output_tokens = provider.get_usage()
    logger.info(f"Выкарыстана {input_tokens} вводу, {cache_tokens} кэшу, {output_tokens} вываду")

if __name__ == "__main__":
    asyncio.run(main()) 