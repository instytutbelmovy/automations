#!/usr/bin/env python3
import os
import argparse
import logging
import glob
from pathlib import Path
from dotenv import load_dotenv
from .epub_parser import EpubParser
from .vert_io import VertIO
from .grammar_db import GrammarDB
from .setup_logging import setup_logging
from .linguistic_bits import SentenceItemType


def convert_epub_to_verti(epub_path: str, output_path: str, logger: logging.Logger) -> None:
    """
    Канвертуе адзін epub файл у verti фармат.

    Args:
        epub_path: Шлях да epub файла
        output_path: Шлях для захавання verti файла
        logger: Logger для запісу паведамленняў
    """
    try:
        logger.info(f"Канвертаванне '{epub_path}' -> '{output_path}'...")
        # Чытаем epub
        parser = EpubParser()
        document = parser.parse(epub_path)

        # Запісваем у verti фармат
        VertIO.write(document, output_path)
        logger.info(f"Файл '{Path(epub_path).name}' паспяхова канвертаваны ў '{output_path}'")
    except Exception as e:
        logger.error(f"Памылка пры канвертацыі файла '{Path(epub_path).name}': {e}")


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
        document = VertIO.read(input_path)

        # Праходзім па ўсіх словах у дакуменце
        processed_count = 0
        for paragraph in document.paragraphs:
            for sentence in paragraph.sentences:
                for item in sentence.items:
                    if item.type == SentenceItemType.Word:
                        # todo only infer compatible with already existing data, say of human has already provided the lemma or some linguistig tags
                        (paradigma_form_id, lemma, linguistic_tags) = grammar_db.infer_grammar_info(item.text)
                        # Аб'ядноўваем з існуючай інфармацыяй, калі яна ёсць
                        item.paradigma_form_id = item.paradigma_form_id.union_with(paradigma_form_id) if item.paradigma_form_id else paradigma_form_id
                        item.lemma = item.lemma or lemma  # Захоўваем першую знойдзеную лему, калі яе не было
                        item.linguistic_tags = item.linguistic_tags.union_with(linguistic_tags) if item.linguistic_tags else linguistic_tags
                        processed_count += 1

        # Запісваем у новы файл
        VertIO.write(document, output_path)
        logger.info(f"Файл '{Path(input_path).name}' паспяхова апрацаваны ({processed_count} слоў) і запісаны ў '{output_path}'")
    except Exception as e:
        logger.error(f"Памылка пры апрацоўцы файла '{Path(input_path).name}': {e}")


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

    # Каманда для канвертацыі epub у verti
    convert_parser = subparsers.add_parser("convert", help="Канвертаваць epub у verti", parents=[io_parser])

    # Каманда для roundtrip тэставання (пакідаем як было)
    roundtrip_parser = subparsers.add_parser("roundtrip", help="Прачытаць verti файл і запісаць яго ў новы файл")
    roundtrip_parser.add_argument("input_path", help="Шлях да ўваходнага verti файла")
    roundtrip_parser.add_argument("output_path", help="Шлях для захавання новага verti файла")

    # Каманда для запаўнення відавочнай граматычнай інфармацыі
    fog_parser = subparsers.add_parser("fog", help="Запаўніць відавочную граматычную інфармацыю", parents=[io_parser])
    fog_parser.add_argument("grammar_base_path", help="Шлях да дырэкторыі з граматычнай базай")

    args = parser.parse_args()

    tasks = []  # Спіс пар (input_file, output_file)

    # Апрацоўваем каманды з гнуткім уваходам/выхадам
    if args.command in ["convert", "fog"]:
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
                else:  # fog
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
                else:  # fog
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
            convert_epub_to_verti(input_f, output_f, logger)
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
            logger.error(f"Памылка загрузкі граматычнай базы: {e}")
            return  # Спыняемся, калі база не загрузілася

        # Выклікаем функцыю апрацоўкі для кожнай задачы
        for input_f, output_f in tasks:
            fill_obvious_grammar(input_f, output_f, grammar_db, logger)

    # Няма патрэбы ў else: parser.print_help(), бо каманда абавязковая


if __name__ == "__main__":
    main()
