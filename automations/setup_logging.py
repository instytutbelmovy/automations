import logging
import sys
from pathlib import Path


def setup_logging(
    log_level="INFO",
    log_file=None,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
):
    """
    Configure logging for the entire application.

    Args:
        log_level: Мінімальны ўзровень лагавання (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Опцыянальны шлях да файла для запісу логаў
        log_format: Фармат паведамленняў лагавання
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Няправільны ровень лагавання: {log_level}")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.INFO)
    logging.getLogger("anthropic").setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger
