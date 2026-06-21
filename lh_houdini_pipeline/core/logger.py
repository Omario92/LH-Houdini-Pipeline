"""
lh_houdini_pipeline.core.logger
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Structured, colour-aware logging for the pipeline.

Provides a thin layer on top of Python's built-in ``logging`` module so
pipeline code gets:

* Named loggers via :func:`get_logger` (same convention as ``__name__``)
* ANSI colour in terminals; degrades gracefully on non-TTY outputs
* Rotating file handler with configurable size / backup count
* Thread-safe :func:`LogContext` context manager for structured fields
* ``setup_pipeline_logging()`` called once at startup to configure handlers

Pure Python -- no ``hou`` imports.  Houdini-specific log sinks (e.g. pushing
messages to the status bar) belong in ``houdini/env.py``.

Example
-------
::

    from lh_houdini_pipeline.core.logger import get_logger, setup_pipeline_logging, LogContext

    setup_pipeline_logging(level="DEBUG", log_file="/tmp/lh_pipeline.log")
    log = get_logger(__name__)

    log.info("Starting texture bake")

    with LogContext(shot="sh0100", asset="hero_car"):
        log.debug("Inside context -- fields appear on every record")
        log.warning("Missing channel", extra={"channel": "roughness"})
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Union


# ---------------------------------------------------------------------------
# ANSI colour map
# ---------------------------------------------------------------------------

_RESET = "\033[0m"
_LEVEL_COLORS: Dict[int, str] = {
    logging.DEBUG:    "\033[36m",    # Cyan
    logging.INFO:     "\033[32m",    # Green
    logging.WARNING:  "\033[33m",    # Yellow
    logging.ERROR:    "\033[31m",    # Red
    logging.CRITICAL: "\033[35m",    # Magenta
}


def _stream_supports_color(stream: Any) -> bool:
    """Return True if *stream* is a TTY that likely renders ANSI codes."""
    return hasattr(stream, "isatty") and stream.isatty()


# ---------------------------------------------------------------------------
# Thread-local context stack
# ---------------------------------------------------------------------------

_local = threading.local()


def _context_stack() -> list:
    if not hasattr(_local, "stack"):
        _local.stack = []
    return _local.stack


def _merged_context() -> Dict[str, Any]:
    """Merge all frames on the current thread's context stack."""
    merged: Dict[str, Any] = {}
    for frame in _context_stack():
        merged.update(frame)
    return merged


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------

# Standard LogRecord attribute names -- used to identify *extra* fields.
_STANDARD_LOG_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
)

_LINE_TMPL = "[{levelname:<8}]  {name}  ::  {message}{ctx}"


class PipelineFormatter(logging.Formatter):
    """Log formatter with optional ANSI colour and structured context fields.

    Output example::

        [INFO    ]  lh_pipeline.file.texture_parser  ::  Starting scan  {asset='hero_car'}

    Args:
        use_color:    ``True`` force colour, ``False`` force plain,
                      ``None`` (default) auto-detect from the attached stream.
        show_context: If ``True``, append thread-local context fields and
                      any caller ``extra`` fields to the log line.
        stream:       The stream this formatter is attached to (used for
                      TTY auto-detection when *use_color* is ``None``).
    """

    def __init__(
        self,
        use_color: Optional[bool] = None,
        show_context: bool = True,
        stream: Any = None,
    ) -> None:
        super().__init__(style="{")
        self._use_color = use_color
        self._show_context = show_context
        self._stream = stream

    def _wants_color(self) -> bool:
        if self._use_color is True:
            return True
        if self._use_color is False:
            return False
        return _stream_supports_color(self._stream or sys.stdout)

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        # Collect structured context
        ctx_str = ""
        if self._show_context:
            ctx: Dict[str, Any] = dict(_merged_context())
            caller_extra = {
                k: v
                for k, v in record.__dict__.items()
                if k not in _STANDARD_LOG_ATTRS and not k.startswith("_")
            }
            ctx.update(caller_extra)
            if ctx:
                pairs = ", ".join(
                    "{k}={v!r}".replace("{k}", k).replace("{v!r}", repr(v))
                    for k, v in sorted(ctx.items())
                )
                ctx_str = "  {" + pairs + "}"

        msg = (
            _LINE_TMPL
            .replace("{levelname:<8}", record.levelname.ljust(8))
            .replace("{name}", record.name)
            .replace("{message}", record.getMessage())
            .replace("{ctx}", ctx_str)
        )

        if self._wants_color():
            color = _LEVEL_COLORS.get(record.levelno, "")
            msg = color + msg + _RESET

        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            msg = msg + "\n" + record.exc_text

        return msg


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

_ROOT_LOGGER_NAME = "lh_pipeline"
_setup_done = False


def setup_pipeline_logging(
    level: Union[str, int] = logging.DEBUG,
    log_file: Optional[Union[str, Path]] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    force: bool = False,
) -> logging.Logger:
    """Configure the pipeline root logger.  Should be called once at startup.

    After this call, all loggers created with :func:`get_logger` will
    automatically inherit these handlers.

    Args:
        level:        Minimum log level for both console and file handlers.
                      Accepts a level name string (``"DEBUG"``) or int.
        log_file:     Optional path for a rotating file log.  Parent
                      directories are created automatically.
        max_bytes:    Maximum size of the log file before rotation (bytes).
        backup_count: Number of rotated backup files to keep.
        force:        Re-configure even if setup has already been done.
                      Useful in interactive Houdini sessions.

    Returns:
        The configured root pipeline ``logging.Logger``.
    """
    global _setup_done

    root = logging.getLogger(_ROOT_LOGGER_NAME)

    if _setup_done and not force:
        return root

    root.handlers.clear()

    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.DEBUG)

    root.setLevel(level)

    # Console handler (colour auto-detected from TTY)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(PipelineFormatter(use_color=None, stream=sys.stdout))
    root.addHandler(console)

    # Optional rotating file handler (no colour)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        fh.setLevel(level)
        fh.setFormatter(PipelineFormatter(use_color=False))
        root.addHandler(fh)

    root.propagate = False
    _setup_done = True
    return root


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """Return a named child of the pipeline root logger.

    Follows Python's standard dot-hierarchy convention.  If *name* doesn't
    already start with the pipeline root prefix, the prefix is prepended::

        log = get_logger(__name__)
        # qualifier: "lh_pipeline.<module_name>"

    If :func:`setup_pipeline_logging` has not been called yet, a
    ``NullHandler`` is added to suppress "No handlers could be found" noise.

    Args:
        name: Logger name, typically ``__name__``.

    Returns:
        A ``logging.Logger`` instance.
    """
    qualified = (
        name
        if name.startswith(_ROOT_LOGGER_NAME)
        else _ROOT_LOGGER_NAME + "." + name
    )
    logger = logging.getLogger(qualified)

    # Ensure a NullHandler on the root if nothing has been configured yet.
    root = logging.getLogger(_ROOT_LOGGER_NAME)
    if not root.handlers:
        root.addHandler(logging.NullHandler())

    return logger


# ---------------------------------------------------------------------------
# LogContext
# ---------------------------------------------------------------------------

@contextmanager
def LogContext(**fields: Any) -> Generator[None, None, None]:
    """Inject structured fields into every log record within this block.

    Fields from nested contexts are merged; inner context wins on key
    conflicts.  The stack is per-thread so concurrent code is safe.

    Args:
        **fields: Arbitrary key-value pairs to attach to log records.

    Example::

        with LogContext(shot="sh0100", task="tex_bake"):
            log.info("baking")
            # record includes: shot='sh0100', task='tex_bake'

        with LogContext(shot="sh0100"):
            with LogContext(frame=1001):
                log.debug("nested")
                # record includes: shot='sh0100', frame=1001
    """
    stack = _context_stack()
    stack.append(fields)
    try:
        yield
    finally:
        stack.pop()
