#!/usr/bin/env python3
import argparse
from pathlib import Path
from .epub_parser import EpubParser
from .vert_io import VertIO

def convert_epub_to_verti(epub_path: str, output_path: str) -> None:
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
    print(f"Файл {epub_path} паспяхова канвертаваны ў {output_path}")

def roundtrip_verti(input_path: str, output_path: str) -> None:
    """
    Чытае verti файл і запісвае яго ў новы файл без зменаў.
    
    Args:
        input_path: Шлях да verti файла
        output_path: Шлях для захавання новага verti файла
    """
    # Чытаем verti файл
    document = VertIO.read(input_path)
    print(document.paragraphs[0])
    # Запісваем у новы файл
    VertIO.write(document, output_path)
    print(f"Файл {input_path} паспяхова прачытаны і запісаны ў {output_path}")

def main():
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
    
    args = parser.parse_args()
    
    if args.command == "convert":
        convert_epub_to_verti(args.epub_path, args.output_path)
    elif args.command == "roundtrip":
        roundtrip_verti(args.input_path, args.output_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 