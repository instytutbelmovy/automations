import pandas as pd
from .linguistic_bits import KorpusDocument
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class MetaReader:
    def __init__(self, excel_path: str):
        """
        Ініцыялізуе чытач мэтаданых з Excel файла.

        Args:
            excel_path: Шлях да Excel файла з мэтаданымі
        """
        self.df = pd.read_excel(excel_path, header=None)  # Чытаем без загалоўкаў
        self.df[0] = pd.to_numeric(self.df[0], errors="coerce")  # Пераўтварэнне ID у лікі

    def get_document_by_id(self, file_id: str | int) -> KorpusDocument | None:
        """
        Атрымлівае мэтаданыя дакумента па яго ID.

        Args:
            file_id: ID дакумента (можа быць радком або лікам)

        Returns:
            KorpusDocument з мэтаданымі або None, калі дакумент не знойдзены
        """
        try:
            file_id = int(file_id)  # Пераўтварэнне ў лік для параўнання
        except (ValueError, TypeError):
            return None

        meta_row = self.df[self.df[0] == file_id]  # ID у слупку A (індекс 0)
        if meta_row.empty:
            return None

        meta = meta_row.iloc[0]
        return KorpusDocument(
            n=file_id,
            title=str(meta[1]) if pd.notna(meta[1]) else "",  # Назва ў слупку B (індекс 1)
            author=None,
            language=None,
            publication_date=str(meta[4]) if pd.notna(meta[4]) else "",  # Дата ў слупку E (індекс 4)
            url=str(meta[2]) if pd.notna(meta[2]) else "",  # URL у слупку C (індекс 2)
            type=str(meta[6]) if pd.notna(meta[6]) else "",  # Тып у слупку G (індекс 6)
            style=str(meta[7]) if pd.notna(meta[7]) else "",  # Стыль у слупку H (індекс 7)
        )

    def get_document_by_filename(self, filename: str) -> KorpusDocument | None:
        """
        Атрымлівае мэтаданыя дакумента па назве файла.

        Args:
            filename: Назва файла

        Returns:
            KorpusDocument з мэтаданымі або None, калі дакумент не знойдзены
        """
        match = re.match(r"^(\d+)", filename)
        if not match:
            logger.warning(f"Не ўдалося знайсці ID у назве файла {filename}")
            return None

        file_id = int(match.group(1))  # Пераўтварэнне ў лік
        return self.get_document_by_id(file_id)
