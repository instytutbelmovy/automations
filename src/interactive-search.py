#!/usr/bin/env python3
"""
Інтэрактыўная праграма для пошуку словаў у граматычнай базе.
"""

import sys
from pathlib import Path
from typing import Optional
from lxml import etree

from grammar_db import GrammarDB


def find_paradigm_location(xml_path: Path, paradigm_tag: str) -> Optional[tuple[int, str]]:
    """
    Пошук месцазнаходжання парадыгмы ў XML файле.
    
    Args:
        xml_path: Шлях да XML файла
        paradigm_tag: Тэг парадыгмы
        
    Returns:
        Картэж (нумар радка, шлях да файла) або None, калі парадыгма не знойдзена
    """
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    
    for elem in root.findall('.//Paradigm'):
        if elem.get('tag') == paradigm_tag:
            return (elem.sourceline, str(xml_path))
    return None


def main():
    if len(sys.argv) != 2:
        print("Выкарыстанне: python interactive-search.py <шлях да дырэкторыі з XML файламі>")
        sys.exit(1)
    
    xml_dir = Path(sys.argv[1])
    if not xml_dir.exists() or not xml_dir.is_dir():
        print(f"Памылка: дырэкторыя {xml_dir} не існуе")
        sys.exit(1)
    
    print("Індэксаванне граматычнай базы...")
    db = GrammarDB()
    db.load_directory(xml_dir)
    print("Індэксаванне завершана. Увядзіце слова для пошуку (або 'q' для выхаду):")
    
    output_format = "tags"
    
    while True:
        word = input("> ").strip()
        if word.lower() == 'q' or word.lower() == 'exit':
            break
            
        if word.lower() == 'details':
            output_format = "details"
            print("Фармат вываду зменены на падрабязны")
            continue
            
        if word.lower() == 'tags':
            output_format = "tags"
            print("Фармат вываду зменены на тэгі")
            continue
            
        variants = db.lookup_word(word)
        if not variants:
            print(f"Слова '{word}' не знойдзена ў базе")
            continue
            
        print(f"\nЗнайдзена {len(variants)} варыянтаў:")
        for i, variant in enumerate(variants, 1):
            meaning_str = f" ({variant.meaning})" if variant.meaning else ""
            if output_format == "details":
                print(f"\n{variant.pos} \"{variant.lemma.replace('+', '\u0301')}\"{meaning_str} {', '.join(variant.form_description)} // {variant.file_name}:{variant.paradigm_line}:{variant.form_line}")
            else:
                print(f"<option number=\"{i}\">{variant.pos} \"{variant.lemma.replace('+', '\u0301')}\"{meaning_str} {', '.join(variant.form_description)}</option>")



if __name__ == '__main__':
    main() 