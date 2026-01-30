import logging
from typing import Optional
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback


class Logger:
    _configured: bool = False

    @staticmethod
    def _configure() -> None:
        if Logger._configured:
            return

        logging.basicConfig(
            level=logging.INFO,
            format="%(name)s: %(message)s",
            datefmt="[%H:%M:%S]",
            handlers=[
                RichHandler(
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                    show_time=True,
                    show_level=True,
                    show_path=False,
                )
            ],
        )

        Logger._configured = True

    @staticmethod
    def _get_logger(source: str) -> logging.Logger:
        Logger._configure()
        return logging.getLogger(source)

    @staticmethod
    def info(message: str, source: str = "System") -> None:
        Logger._get_logger(source).info(message)

    @staticmethod
    def warn(message: str, source: str = "System") -> None:
        Logger._get_logger(source).warning(message)

    @staticmethod
    def debug(message: str, source: str = "System") -> None:
        Logger._get_logger(source).debug(message)

    @staticmethod
    def error(
        message: str,
        source: str = "System",
        exc: Optional[BaseException] = None,
    ) -> None:
        logger = Logger._get_logger(source)
        if exc is not None:
            logger.error(message, exc_info=exc)
        else:
            logger.error(message)
