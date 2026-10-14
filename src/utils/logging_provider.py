import sys
from pathlib import Path

from loguru import logger


def get_logger(name: str):
    """
    Configura o logger para registrar mensagens de log em um arquivo e no console.
    Args:
        name (str): O nome do logger.

    """
    logger.remove()

    logger.add(
        sys.stderr,
        format=(
            "[<green>{time:DD-MM-YYYY HH:mm:ss}</green>] >> "
            "<yellow>{level}</yellow> >> "
            "<level>{name}:{line}</level> >> "
            "<cyan>{message}</cyan>"
        ),
        level="INFO",
        colorize=True,
        serialize=True
    )

    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / "ad-automation.log",
        rotation="5 MB",
        retention="7 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} >> {level} >> {name}:{function}:{line} >> "
               "{message}",
        level="DEBUG",
        )

    return logger

if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.info("Testando o logger")