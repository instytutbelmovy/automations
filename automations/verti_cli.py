#!/usr/bin/env python3
import os
import argparse
import logging
import glob
import traceback
from pathlib import Path
from dotenv import load_dotenv
from .doc_parser import DocParser
from .docx_reader import DocxReader
from .pdf_reader import PdfReader
from .txt_reader import TxtReader
from .epub_reader import EpubReader
from .vert_io import VertIO
from .grammar_db import GrammarDB
from .setup_logging import setup_logging
from .linguistic_bits import SentenceItemType
import pandas as pd
import re
from .meta_reader import MetaReader


def convert_to_verti(input_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Канвертуе файл у verti фармат. Тып файла вызначаецца па пашырэнні.

    Args:
        input_path: Шлях да ўваходнага файла
        output_path: Шлях для захавання verti файла
        logger: Logger для запісу паведамленняў
    """
    try:
        logger.info(f"Канвертаванне '{input_path}' -> '{output_path}'...")

        # Вызначаем тып файла па пашырэнні
        file_extension = Path(input_path).suffix.lower()

        # Выбіраем адпаведны чытач
        reader_class = None
        if file_extension == ".epub":
            reader_class = EpubReader
        elif file_extension == ".txt":
            reader_class = TxtReader
        elif file_extension == ".docx":
            reader_class = DocxReader
        elif file_extension == ".pdf":
            reader_class = PdfReader
        else:
            logger.info(f"Прапускаем '{Path(input_path).name}'")
            return

        # Ствараем парсер з адпаведным чытачом
        parser = DocParser(reader_class)

        # Чытаем файл
        document = parser.parse(input_path)

        # Запісваем у verti фармат
        VertIO.write_verti(document, output_path)
        logger.info(f"Файл '{Path(input_path).name}' паспяхова канвертаваны ў '{output_path}'")
    except Exception as e:
        logger.error(f"Памылка пры канвертацыі файла '{Path(input_path).name}': {e}\n{traceback.format_exc()}")


def roundtrip_verti(input_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Чытае verti файл і запісвае яго ў новы файл без зменаў.

    Args:
        input_path: Шлях да verti файла
        output_path: Шлях для захавання новага verti файла
    """
    # Чытаем verti файл
    document = VertIO.read_verti(input_path)

    # Запісваем у новы файл
    VertIO.write_verti(document, output_path)
    logger.info(f"Файл {input_path} паспяхова прачытаны і запісаны ў {output_path}")


def fill_obvious_grammar(input_path: str, output_path: str, grammar_db: GrammarDB, logger: logging.Logger) -> None:
    """
    Запаўняе відавочную граматычную інфармацыю для слоў у адным verti файле.

    Args:
        input_path: Шлях да verti файла
        output_path: Шлях для захавання новага verti файла
        grammar_db: Загружаная граматычная база
        logger: Logger для запісу паведамленняў
    """
    try:
        logger.info(f"Апрацоўка '{input_path}' -> '{output_path}'...")
        # Чытаем verti файл
        document = VertIO.read_verti(input_path)

        # Праходзім па ўсіх словах у дакуменце
        processed_count = 0
        for paragraph in document.paragraphs:
            for sentence in paragraph.sentences:
                for item in sentence.items:
                    if item.type == SentenceItemType.Word:
                        # todo only infer compatible with already existing data, say of human has already provided the lemma or some linguistig tags
                        (paradigma_form_id, lemma, linguistic_tag) = grammar_db.infer_grammar_info(item.text)
                        # Аб'ядноўваем з існуючай інфармацыяй, калі яна ёсць
                        item.paradigma_form_id = item.paradigma_form_id.union_with(paradigma_form_id) if item.paradigma_form_id else paradigma_form_id
                        item.lemma = item.lemma or lemma  # Захоўваем першую знойдзеную лему, калі яе не было
                        item.linguistic_tag = item.linguistic_tag.union_with(linguistic_tag) if item.linguistic_tag else linguistic_tag
                        processed_count += 1

        # Запісваем у новы файл
        VertIO.write_verti(document, output_path)
        logger.info(f"Файл '{Path(input_path).name}' паспяхова апрацаваны ({processed_count} слоў) і запісаны ў '{output_path}'")
    except Exception as e:
        logger.error(f"Памылка пры апрацоўцы файла '{Path(input_path).name}': {e}\n{traceback.format_exc()}")


def convert_verti_to_vert(input_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Канвертуе verti файл у vert фармат.

    Args:
        input_path: Шлях да verti файла
        output_path: Шлях для захавання vert файла
        logger: Logger для запісу паведамленняў
    """
    try:
        logger.info(f"Канвертаванне '{input_path}' -> '{output_path}' (vert)...")
        # Чытаем verti файл
        document = VertIO.read_verti(input_path)

        # Запісваем у vert фармат
        VertIO.write_vert(document, output_path)
        logger.info(f"Файл '{Path(input_path).name}' паспяхова канвертаваны ў vert фармат: '{output_path}'")
    except Exception as e:
        logger.error(f"Памылка пры канвертацыі файла '{Path(input_path).name}' у vert: {e}\n{traceback.format_exc()}")


def fill_meta(input_path: str, meta_path: str, overwrite: bool, logger: logging.Logger) -> None:
    """
    Запоўніць мэтаданыя з Excel файла для verti/vert файлаў.

    Args:
        input_path: Шлях да ўваходнага файла ці glob-узор
        meta_path: Шлях да Excel файла з мэтаданымі
        overwrite: Ці перазапісваць існуючыя мэтаданыя
        logger: Логер для запісу паведамленняў
    """
    # Загрузка мэтаданых з Excel
    meta_reader = MetaReader(meta_path)

    # Знаходжанне ўсіх файлаў па glob-узору
    input_files = list(Path().glob(input_path))
    if not input_files:
        logger.error(f"Не знойдзена файлаў па ўзоры {input_path}")
        return

    for file_path in input_files:
        # Атрыманне мэтаданых па назве файла
        meta_doc = meta_reader.get_document_by_filename(file_path.name)
        if not meta_doc:
            logger.warning(f"Не знойдзена мэтаданых для файла {file_path.name}")
            continue

        # Абнаўленне мэтаданых у файле
        try:
            VertIO.update_doc_header(str(file_path), meta_doc, overwrite)
            logger.info(f"Абноўлены мэтаданыя для файла {file_path.name}")
        except Exception as e:
            logger.error(f"Памылка пры абнаўленні мэтаданых для файла {file_path.name}: {e}\n{traceback.format_exc()}")


def main():
    load_dotenv()
    log_level = os.getenv("LOG_LEVEL", "INFO")
    setup_logging(log_level)  # Наладжваем лагаванне раней
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Утыліта для працы з verti файламі")
    subparsers = parser.add_subparsers(dest="command", help="Каманда для выканання", required=True)  # Робім каманду абавязковай

    # Агульны парсер для каманд, якія патрабуюць уваход/выхад
    io_parser = argparse.ArgumentParser(add_help=False)
    io_parser.add_argument("input", help="Шлях да ўваходнага файла або glob шаблон (напр., 'кнігі/*.epub' або 'file.epub')")
    io_parser.add_argument("output", help="Шлях да выхаднога файла або дырэкторыі")

    # Каманда для канвертацыі ў verti
    convert_parser = subparsers.add_parser("convert", help="Канвертаваць файл у verti (падтрымліваюцца epub, txt, docx і pdf)", parents=[io_parser])

    # Каманда для roundtrip тэставання (пакідаем як было)
    roundtrip_parser = subparsers.add_parser("roundtrip", help="Прачытаць verti файл і запісаць яго ў новы файл")
    roundtrip_parser.add_argument("input_path", help="Шлях да ўваходнага verti файла")
    roundtrip_parser.add_argument("output_path", help="Шлях для захавання новага verti файла")

    # Каманда для запаўнення відавочнай граматычнай інфармацыі
    fog_parser = subparsers.add_parser("fog", help="Запаўніць відавочную граматычную інфармацыю", parents=[io_parser])
    fog_parser.add_argument("grammar_base_path", help="Шлях да дырэкторыі з граматычнай базай")

    # Каманда для канвертацыі verti ў vert
    tovert_parser = subparsers.add_parser("tovert", help="Канвертаваць verti у vert", parents=[io_parser])

    # Каманда для запоўнення мэтаданых
    fill_meta_parser = subparsers.add_parser("fill-meta", help="Запаўніць мэтаданыя з Excel файла для verti/vert файлаў", parents=[io_parser])
    fill_meta_parser.add_argument("meta_path", help="Шлях да Excel файла з мэтаданымі")
    fill_meta_parser.add_argument("--overwrite-meta", action="store_true", help="Перазапісваць існуючыя мэтаданыя")

    args = parser.parse_args()

    tasks = []  # Спіс пар (input_file, output_file)

    # Апрацоўваем каманды з гнуткім уваходам/выхадом
    if args.command in ["convert", "fog", "tovert", "fill-meta"]:
        input_spec = args.input
        output_spec = args.output

        input_files = glob.glob(input_spec, recursive=True)
        if not input_files:
            logger.warning(f"Па шаблоне/шляху '{input_spec}' не знойдзена файлаў.")
            return

        output_path = Path(output_spec)
        is_multiple_inputs = len(input_files) > 1

        if is_multiple_inputs:
            # Выхад ПАВІНЕН быць дырэкторыяй
            if output_path.exists() and not output_path.is_dir():
                logger.error(f"Памылка: Выхадны шлях '{output_spec}' павінен быць дырэкторыяй пры апрацоўцы некалькіх файлаў.")
                return
            # Пераканаемся, што дырэкторыя існуе
            output_path.mkdir(parents=True, exist_ok=True)
            output_dir = output_path

            for input_file_str in input_files:
                input_file = Path(input_file_str)
                # Вызначаем імя выхаднога файла
                if args.command == "convert":
                    output_filename = input_file.stem + ".verti"
                elif args.command == "tovert":
                    output_filename = input_file.stem + ".vert"
                else:  # fog or fill-meta
                    output_filename = input_file.name
                output_file = output_dir / output_filename
                tasks.append((str(input_file), str(output_file)))
        else:  # Адзін уваходны файл
            input_file = Path(input_files[0])
            # Вызначаем, ці з'яўляецца выхадны шлях файлам або дырэкторыяй
            if output_path.is_dir() or (not output_path.exists() and output_spec.endswith(os.sep)):  # Калі шлях заканчваецца на / ці \ - гэта дырэкторыя
                # Выхад - дырэкторыя
                output_dir = output_path
                output_dir.mkdir(parents=True, exist_ok=True)
                if args.command == "convert":
                    output_filename = input_file.stem + ".verti"
                elif args.command == "tovert":
                    output_filename = input_file.stem + ".vert"
                else:  # fill-meta
                    output_filename = input_file.name
                output_file = output_dir / output_filename
                tasks.append((str(input_file), str(output_file)))
            else:
                # Выхад - файл
                output_file = output_path
                # Пераканаемся, што бацькоўская дырэкторыя існуе
                output_file.parent.mkdir(parents=True, exist_ok=True)
                tasks.append((str(input_file), str(output_file)))

    # --- Выкананне задач ---
    if args.command == "convert":
        for input_f, output_f in tasks:
            convert_to_verti(input_f, output_f, logger)
    elif args.command == "roundtrip":
        roundtrip_verti(args.input_path, args.output_path, logger)
    elif args.command == "fog":
        # Загружаем базу адзін раз
        logger.info(f"Індэксацыя граматычнай базы '{args.grammar_base_path}'...")
        grammar_db = GrammarDB()
        try:
            grammar_db.load_directory(Path(args.grammar_base_path))
            logger.info(f"Індэксацыя граматычнай базы выканана")
        except Exception as e:
            logger.error(f"Памылка загрузкі граматычнай базы: {e}\n{traceback.format_exc()}")
            return  # Спыняемся, калі база не загрузілася

        # Выклікаем функцыю апрацоўкі для кожнай задачы
        for input_f, output_f in tasks:
            fill_obvious_grammar(input_f, output_f, grammar_db, logger)
    elif args.command == "tovert":
        for input_f, output_f in tasks:
            convert_verti_to_vert(input_f, output_f, logger)
    elif args.command == "fill-meta":
        fill_meta(args.input, args.meta_path, args.overwrite_meta, logger)

    # Няма патрэбы ў else: parser.print_help(), бо каманда абавязковая


if __name__ == "__main__":
    main()
