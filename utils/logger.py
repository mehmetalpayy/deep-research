import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

_console = Console(file=sys.stderr)


class Logger:
    def __init__(self, name: str = "deep_research", level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = RichHandler(
                console=_console,
                show_time=True,
                show_level=True,
                show_path=False,
                omit_repeated_times=False,
                markup=False,
                rich_tracebacks=True,
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(level)
            self._logger.propagate = False

    def info(self, message: str) -> None:
        self._logger.info(message, stacklevel=2)

    def debug(self, message: str) -> None:
        self._logger.debug(message, stacklevel=2)

    def warn(self, message: str) -> None:
        self._logger.warning(message, stacklevel=2)

    def error(self, message: str) -> None:
        self._logger.error(message, stacklevel=2)

    def exception(self, message: str) -> None:
        self._logger.exception(message, stacklevel=2)
