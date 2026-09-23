import logging
import sys
from pathlib import Path
app = Path(__file__).parent.parent / "logs" / "app.log"

def get_logger(name: str):
    """
    Configura o logger para registrar mensagens de log em um arquivo e no console.
    Args:
        name (str): O nome do logger.

    """
    fmt = logging.Formatter(
        "{asctime} - {levelname} - {name} - {message}",
        style="{",
        datefmt="%d/%m/%Y %H:%M"
    )

    file_handler = logging.FileHandler(app, encoding="utf-8")
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

    return logging.getLogger(name)

if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.info("Testando o logger")