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
    
    while True:
        word = input("> ").strip()
        if word.lower() == 'q':
            break
            
        variants = db.lookup_word(word)
        if not variants:
            print(f"Слова '{word}' не знойдзена ў базе")
            continue
            
        print(f"\nЗнайдзена {len(variants)} варыянтаў:")
        for i, variant in enumerate(variants, 1):
            print(f"\nВарыянт {i}:")
            print(f"Частка мовы: {variant.pos}")
            print(f"Лема: {variant.variant_lemma}")
            print(f"Тэг парадыгмы: {variant.paradigm_tag}")
            print(f"ID парадыгмы: {variant.paradigm_id}")
            print(f"ID варыянту: {variant.variant_id}")
            print(f"Тэг формы: {variant.form_tag}")
            print(f"Нумар радка парадыгмы: {variant.paradigm_line}")
            print(f"Нумар радка формы: {variant.form_line}")
            print(f"Файл: {variant.file_name}")
            print("Граматычныя ўласцівасці:")
            for prop, value in variant.properties.items():
                print(f"  {prop}: {value}")



if __name__ == '__main__':
    main() 