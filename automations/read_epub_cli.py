#!/usr/bin/env python3
import sys
from pathlib import Path
from .epub_reader import EpubReader
import platform
import termios
import tty
import sys

def get_key():
    """Вяртае націснутую клавішу."""
    if platform.system() == 'Windows':
        import msvcrt
        return msvcrt.getch().decode('utf-8')
    else:
        # Для Linux/Mac
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def print_paragraphs_interactive(paragraphs):
    """Паказвае параграфы па адным пасля націску клавішы."""
    print("\n=== Інтэрактыўнае чытанне ===")
    print("Націсніце любую клавішу для прагляду наступнага параграфа")
    print("Націсніце 'q' для выхаду")
    print("-" * 50)

    for i, paragraph in enumerate(paragraphs, 1):
        print(f"\nПараграф {i}:")
        print("-" * 50)
        print(paragraph)
        
        key = get_key()
        if key.lower() == 'q':
            print("\nЧытанне спынена")
            break

def main():
    if len(sys.argv) != 2:
        print("Выкарыстанне: python -m automations.read_epub <шлях_да_epub_файла>")
        sys.exit(1)

    epub_path = Path(sys.argv[1])
    if not epub_path.exists():
        print(f"Памылка: файл {epub_path} не існуе")
        sys.exit(1)

    try:
        reader = EpubReader()
        document = reader.read(epub_path)

        print("\n=== Метададзеныя ===")
        print(f"Назва: {document.title}")
        if document.author:
            print(f"Аўтар: {document.author}")
        if document.language:
            print(f"Мова: {document.language}")
        if document.publication_date:
            print(f"Дата публікацыі: {document.publication_date}")

        print("\n=== Змесціва ===")
        print(f"Усяго параграфаў: {len(document.paragraphs)}")
        
        print_paragraphs_interactive(document.paragraphs)

    except Exception as e:
        print(f"Памылка пры чытанні файла: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 