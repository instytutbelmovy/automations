#!/usr/bin/env python3
import os
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv
from .epub_parser import EpubParser
from .vert_io import VertIO
from .grammar_db import GrammarDB
from .setup_logging import setup_logging
from .linguistic_bits import SentenceItemType


def convert_epub_to_verti(epub_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Канвертуе epub файл у verti фармат.

    Args:
        epub_path: Шлях да epub файла
        output_path: Шлях для захавання verti файла
    """
    # Чытаем epub
    parser = EpubParser()
    document = parser.parse(epub_path)

    # Запісваем у verti фармат
    VertIO.write(document, output_path)
    logger.info(f"Файл {epub_path} паспяхова канвертаваны ў {output_path}")


def roundtrip_verti(input_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Чытае verti файл і запісвае яго ў новы файл без зменаў.

    Args:
        input_path: Шлях да verti файла
        output_path: Шлях для захавання новага verti файла
    """
    # Чытаем verti файл
    document = VertIO.read(input_path)

    # Запісваем у новы файл
    VertIO.write(document, output_path)
    logger.info(f"Файл {input_path} паспяхова прачытаны і запісаны ў {output_path}")


def fill_obvious_grammar(input_path: str, output_path: str, grammar_base_path: str, logger: logging.Logger) -> None:
    """
    Запаўняе відавочную граматычную інфармацыю для слоў у verti файле.

    Args:
        input_path: Шлях да verti файла
        output_path: Шлях для захавання новага verti файла
        grammar_base_path: Шлях да дырэкторыі з граматычнай базай
    """
    # Загружаем граматычную базу
    logger.info(f"Індэксацыя граматычнай базы...")
    grammar_db = GrammarDB()
    grammar_db.load_directory(Path(grammar_base_path))
    logger.info(f"Індэксацыя граматычнай базы выканана")

    # Чытаем verti файл
    document = VertIO.read(input_path)

    # Праходзім па ўсіх словах у дакуменце
    for paragraph in document.paragraphs:
        for sentence in paragraph.sentences:
            for item in sentence.items:
                if item.type == SentenceItemType.Word:
                    (paradigma_form_id, lemma, linguistic_tags) = grammar_db.infer_grammar_info(item.text)
                    item.paradigma_form_id = item.paradigma_form_id.union_with(paradigma_form_id) if item.paradigma_form_id else paradigma_form_id
                    item.lemma = item.lemma or lemma
                    item.linguistic_tags = item.linguistic_tags.union_with(linguistic_tags) if item.linguistic_tags else linguistic_tags

    # Запісваем у новы файл
    VertIO.write(document, output_path)
    logger.info(f"Файл {input_path} паспяхова апрацаваны і запісаны ў {output_path}")


def main():
    load_dotenv()

    log_level = os.getenv("LOG_LEVEL", "INFO")

    parser = argparse.ArgumentParser(description="Утыліта для працы з verti файламі")
    subparsers = parser.add_subparsers(dest="command", help="Каманда для выканання")

    # Каманда для канвертацыі epub у verti
    convert_parser = subparsers.add_parser("convert", help="Канвертаваць epub у verti")
    convert_parser.add_argument("epub_path", help="Шлях да epub файла")
    convert_parser.add_argument("output_path", help="Шлях для захавання verti файла")

    # Каманда для roundtrip тэставання
    roundtrip_parser = subparsers.add_parser("roundtrip", help="Прачытаць verti файл і запісаць яго ў новы файл")
    roundtrip_parser.add_argument("input_path", help="Шлях да verti файла")
    roundtrip_parser.add_argument("output_path", help="Шлях для захавання новага verti файла")

    # Каманда для запаўнення відавочнай граматычнай інфармацыі
    fog_parser = subparsers.add_parser("fog", help="Запаўніць відавочную граматычную інфармацыю (fill obvious grammar)")
    fog_parser.add_argument("input_path", help="Шлях да verti файла")
    fog_parser.add_argument("output_path", help="Шлях для захавання новага verti файла")
    fog_parser.add_argument("grammar_base_path", help="Шлях да дырэкторыі з граматычнай базай")

    args = parser.parse_args()

    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    if args.command == "convert":
        convert_epub_to_verti(args.epub_path, args.output_path, logger=logger)
    elif args.command == "roundtrip":
        roundtrip_verti(args.input_path, args.output_path, logger=logger)
    elif args.command == "fog":
        fill_obvious_grammar(args.input_path, args.output_path, args.grammar_base_path, logger=logger)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
