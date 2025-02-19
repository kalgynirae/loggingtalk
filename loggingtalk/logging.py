from __future__ import annotations

import logging
import os
import shlex
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import InitVar, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

logger = logging.getLogger(__name__)


def configure_logging(
    level: int,
    *,
    colors: bool = True,
    prefixes: bool = True,
    replace_newlines: bool = True,
    subprocesses: bool = True,
) -> None:
    # The logger hierarchy mirrors the module hierarchy, making it easy
    # to control logs from libraries.
    if not os.getenv("PYTHONASYNCIODEBUG"):
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    prefix_format = "%(prefix)s" if prefixes else ""
    fmt = f"%(asctime)s %(levelname)10s: {prefix_format}%(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    color_formatter = Formatter(
        fmt=fmt,
        datefmt=datefmt,
        include_color_escapes=colors,
        replace_newlines=replace_newlines,
    )
    plain_formatter = Formatter(
        fmt=fmt,
        datefmt=datefmt,
        include_color_escapes=False,
        replace_newlines=replace_newlines,
    )

    file_handler = logging.FileHandler("logs/loggingtalk.log")
    file_handler.setFormatter(color_formatter)

    plain_handler = logging.FileHandler("logs/loggingtalk-plain.log")
    plain_handler.setFormatter(plain_formatter)

    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(color_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(plain_handler)
    root_logger.addHandler(stderr_handler)

    root_logger.setLevel(logging.DEBUG)
    stderr_handler.setLevel(level)

    if colors:
        logging.setLogRecordFactory(FormattingLogRecord)

    if prefixes:
        file_handler.addFilter(PrefixFilter())
        plain_handler.addFilter(PrefixFilter())
        stderr_handler.addFilter(PrefixFilter())

    if subprocesses:
        sys.addaudithook(log_subprocess_execs)


_current_prefix = ContextVar("_current_prefix")


@contextmanager
def log_prefix(prefix: str) -> Iterator[None]:
    existing = _current_prefix.get("")
    token = _current_prefix.set(existing + prefix)
    try:
        yield
    finally:
        _current_prefix.reset(token)


class PrefixFilter(logging.Filter):
    """Filter that adds the current prefix to each log record"""

    def filter(self, record):
        record.prefix = _current_prefix.get("")
        return True


class Color(Enum):
    red = 1
    green = 2
    yellow = 3
    blue = 4
    magenta = 5
    cyan = 6


@dataclass(frozen=True)
class Format:
    color: Color | None = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underlined: bool = False

    def apply(self, value: object) -> Formatted:
        return Formatted(value, self)

    def make_formatter(self) -> Callable[[str], str]:
        parts: list[str] = []
        reset_parts: list[str] = []
        labels: list[str] = []
        if self.color:
            parts.append(f"3{self.color.value}")
            reset_parts.append("39")
            labels.append(self.color.name)
        if self.bold:
            parts.append("1")
            reset_parts.append("22")
            labels.append("bold")
        if self.dim:
            parts.append("2")
            reset_parts.append("22")
            labels.append("dim")
        if self.italic:
            parts.append("3")
            reset_parts.append("23")
            labels.append("italic")
        if self.underlined:
            parts.append("4")
            reset_parts.append("24")
            labels.append("underlined")

        if not parts:
            return str

        escape = f"\x1b[{';'.join(parts)}m"
        reset = f"\x1b[{';'.join(reset_parts)}m"
        name = f"format_{'_'.join(labels)}"

        def func(s: str) -> str:
            return escape + s + reset

        func.__name__ = name
        func.__qualname__ = func.__qualname__.replace("func", name)
        return func


@dataclass(frozen=True)
class Formatted:
    value: object
    formatter: Callable[[str], str] = field(
        init=False, repr=False, hash=False, compare=False
    )
    format: InitVar[Format]

    def __post_init__(self, format: Format) -> str:
        object.__setattr__(self, "formatter", format.make_formatter())

    def __repr__(self) -> str:
        return repr(self.value)

    def __str__(self) -> str:
        return str(self.value)

    def activate(self) -> _ActivatedFormatted:
        return _ActivatedFormatted(self.value, self.formatter)


@dataclass(frozen=True)
class _ActivatedFormatted:
    value: object
    formatter: Callable[[str], str]

    def __repr__(self) -> str:
        return self.formatter(repr(self.value))

    def __str__(self) -> str:
        return self.formatter(str(self.value))


FORMATS: list[tuple[type, Format]] = [
    (datetime, Format(color=Color.yellow)),
    (Path, Format(color=Color.cyan)),
]


T = TypeVar("T")


def format_in_logs(**kwargs) -> Callable[[T], T]:
    format = Format(**kwargs)

    def _format_in_logs_decorator(type: T) -> T:
        FORMATS.append((type, format))
        return type

    return _format_in_logs_decorator


def _format_arg(arg: T) -> T | Formatted:
    if isinstance(arg, Formatted):
        return arg.activate()
    for type, format in FORMATS:
        if isinstance(arg, type):
            return _ActivatedFormatted(arg, format.make_formatter())
    else:
        return arg


_use_color = ContextVar("_use_color")


class FormattingLogRecord(logging.LogRecord):
    def getMessage(self):
        msg = str(self.msg)
        # Logging calls allow passing a single dict argument directly so that keyword
        # placeholders can be used in the message. We don't support formatting in that
        # case (for now). TODO: Consider supporting this.
        if isinstance(self.args, dict):
            msg = msg % self.args
        elif isinstance(self.args, tuple):
            if _use_color.get(False):
                formatted_args = tuple(map(_format_arg, self.args))
                msg = msg % formatted_args
            else:
                msg = msg % self.args
        else:
            print(
                f"FormattingLogRecord: Unexpected type for self.args ({type(self.args).__name__})",
                file=sys.stderr,
            )
        return msg


@format_in_logs(dim=True)
@dataclass(frozen=True)
class SubprocessArgs:
    args: str | list[str]

    def __str__(self) -> str:
        if isinstance(self.args, str):
            return self.args
        return f"«{shlex.join(self.args)}»"


def log_subprocess_execs(event_name: str, event_args: Any) -> None:
    if event_name == "subprocess.Popen":
        executable, args, cwd, env = event_args
        extra_message_parts = []
        extra_args = []
        if cwd is not None:
            extra_message_parts.append("cwd: %s")
            extra_args.append(Path(cwd))
        if env is not None:
            extra_message_parts.append("env: %s")
            extra_args.append(Format(color=Color.yellow).apply(env))
        extra_message = (
            f" ({', '.join(extra_message_parts)})" if extra_message_parts else ""
        )
        logger.info(f"Running %s{extra_message}", SubprocessArgs(args), *extra_args)


class Formatter(logging.Formatter):
    def __init__(
        self,
        fmt: str,
        datefmt: str,
        *args,
        include_color_escapes: bool,
        replace_newlines: bool,
        **kwargs,
    ) -> None:
        super().__init__(fmt, datefmt, *args, **kwargs)
        self.include_color_escapes = include_color_escapes
        self.replace_newlines = replace_newlines

    def format(self, record: logging.LogRecord) -> str:
        token = _use_color.set(self.include_color_escapes)
        try:
            s = super().format(record)
        finally:
            _use_color.reset(token)

        return s.replace("\n", "␤") if self.replace_newlines else s
