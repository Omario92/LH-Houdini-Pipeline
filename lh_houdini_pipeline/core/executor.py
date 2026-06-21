"""
lh_houdini_pipeline.core.executor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Safe, logged subprocess execution with dry-run, timeout, retry, and
non-blocking support.

Design
------
* ``CommandResult``    -- frozen dataclass capturing all process output.
  ``.raise_on_error()`` enables clean chaining.
* ``RetryPolicy``      -- separate dataclass for retry strategy (not tangled
  into ``Executor``), so it can be passed around, serialised, or swapped.
* ``Executor``         -- synchronous subprocess runner.  Instantiated with
  configuration (dry_run, timeout, env) rather than passing per-call so
  callers can keep a "baked" executor for a specific tool (e.g. maketx).
* ``ThreadedExecutor`` -- wraps ``Executor.run()`` in a ``threading.Thread``
  with callbacks.  No asyncio dependency -- Houdini's Python environment
  doesn't guarantee a running event loop.
* ``dry_run=True``     -- logs the command but never spawns a process.
  Essential during pipeline development and unit-testing.

Pure Python -- no ``hou`` imports.

Example
-------
::

    from lh_houdini_pipeline.core.executor import Executor, RetryPolicy

    exe = Executor(timeout=120, retry=RetryPolicy(max_attempts=3, delay=2.0))
    result = exe.run(["maketx", "-v", "input.exr", "-o", "output.tx"])
    result.raise_on_error()
    print(result.stdout)
"""

from __future__ import annotations

import shlex
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from lh_houdini_pipeline.core.logger import get_logger

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# CommandResult
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CommandResult:
    """Immutable record of a completed subprocess invocation.

    Attributes:
        command:    The command as a list of strings.
        returncode: Process exit code (0 == success by convention).
        stdout:     Captured standard output (stripped of leading/trailing
                    whitespace).
        stderr:     Captured standard error (stripped).
        duration:   Wall-clock seconds the process took.
        dry_run:    ``True`` if the process was never actually spawned.
        error:      Python exception if the process couldn't be started
                    (e.g. executable not found).  ``None`` on normal completion.
    """
    command:    List[str]
    returncode: int                 = 0
    stdout:     str                 = ""
    stderr:     str                 = ""
    duration:   float               = 0.0
    dry_run:    bool                = False
    error:      Optional[Exception] = field(default=None, compare=False)

    @property
    def success(self) -> bool:
        """``True`` if exit code is 0 and no Python-level exception occurred."""
        return self.returncode == 0 and self.error is None

    @property
    def command_str(self) -> str:
        """Shell-quoted command string suitable for display or logging."""
        return shlex.join(self.command)

    def raise_on_error(self) -> "CommandResult":
        """Raise :exc:`ExecutionError` if the command failed; return *self* otherwise.

        Enables clean chaining::

            result = exe.run(["maketx", ...]).raise_on_error()
            # only reaches here on success
        """
        if not self.success:
            raise ExecutionError(self)
        return self


class ExecutionError(RuntimeError):
    """Raised by :py:meth:`CommandResult.raise_on_error` on failure."""

    def __init__(self, result: CommandResult) -> None:
        self.result = result
        lines = [
            f"Command failed (exit {result.returncode}): {result.command_str}",
        ]
        if result.stderr:
            lines.append(f"stderr: {result.stderr[:1000]}")
        if result.error:
            lines.append(f"OS error: {result.error}")
        super().__init__("\n".join(lines))


# ---------------------------------------------------------------------------
# RetryPolicy
# ---------------------------------------------------------------------------

@dataclass
class RetryPolicy:
    """Controls retry behaviour for commands that may transiently fail.

    Attributes:
        max_attempts:    Total attempts including the first.  Set to 1 to
                         disable retries.
        delay:           Seconds to wait before the second attempt.
        backoff:         Multiplier applied to *delay* after each failure.
                         ``1.0`` = constant interval; ``2.0`` = exponential.
        retryable_codes: Exit codes that should trigger a retry.  An empty
                         frozenset means retry on *any* non-zero exit code.
    """
    max_attempts:    int       = 3
    delay:           float     = 1.0
    backoff:         float     = 2.0
    retryable_codes: frozenset = field(default_factory=frozenset)


# Convenience singleton: no retries.
NO_RETRY = RetryPolicy(max_attempts=1)


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------

class Executor:
    """Runs subprocesses with logging, timeout, dry-run, and optional retry.

    Args:
        timeout:     Maximum seconds per attempt.  ``None`` means unlimited.
        dry_run:     If ``True``, log the command but never spawn a process.
                     Returns a synthetic success ``CommandResult``.
        env:         Extra environment variables merged on top of the current
                     process environment for every call.  ``None`` = inherit.
        cwd:         Working directory for spawned processes.  ``None`` = inherit.
        retry:       :class:`RetryPolicy` to apply on failure.
        log_stdout:  Forward captured stdout through the logger at DEBUG.
        log_stderr:  Forward captured stderr through the logger at WARNING.
    """

    def __init__(
        self,
        timeout: Optional[float] = None,
        dry_run: bool = False,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[Union[str, Path]] = None,
        retry: RetryPolicy = NO_RETRY,
        log_stdout: bool = True,
        log_stderr: bool = True,
    ) -> None:
        self.timeout    = timeout
        self.dry_run    = dry_run
        self.env        = env
        self.cwd        = str(cwd) if cwd else None
        self.retry      = retry
        self.log_stdout = log_stdout
        self.log_stderr = log_stderr

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        command: Sequence[str],
        extra_env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> CommandResult:
        """Run *command* synchronously and return a :class:`CommandResult`.

        This method never raises; call ``.raise_on_error()`` on the result
        if you want an exception on failure.

        Args:
            command:   Command and arguments as a sequence of strings.
                       Never passed through a shell -- no injection risk.
            extra_env: Per-call env vars merged on top of ``self.env``.
            timeout:   Per-call timeout override.  Defaults to ``self.timeout``.

        Returns:
            A :class:`CommandResult` (always returned, never raised).
        """
        cmd = list(command)
        eff_timeout = timeout if timeout is not None else self.timeout

        if self.dry_run:
            _log.info("[DRY-RUN] %s", shlex.join(cmd))
            return CommandResult(command=cmd, dry_run=True)

        merged_env = self._build_env(extra_env)
        policy = self.retry
        attempt = 0
        delay = policy.delay
        last: Optional[CommandResult] = None

        while attempt < policy.max_attempts:
            attempt += 1
            if attempt > 1:
                _log.debug(
                    "Retry %d/%d for: %s",
                    attempt, policy.max_attempts, shlex.join(cmd),
                )
                time.sleep(delay)
                delay = delay * policy.backoff

            last = self._run_once(cmd, merged_env, eff_timeout)
            if last.success:
                return last

            # Decide whether this failure warrants a retry
            retryable = (
                not policy.retryable_codes
                or last.returncode in policy.retryable_codes
            )
            if not retryable or attempt >= policy.max_attempts:
                break

        return last  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_once(
        self,
        cmd: List[str],
        env: Optional[Dict[str, str]],
        timeout: Optional[float],
    ) -> CommandResult:
        """Execute *cmd* exactly once and return the result."""
        import logging as _logging

        _log.debug("Executing: %s", shlex.join(cmd))
        t0 = time.monotonic()

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=self.cwd,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            dur = time.monotonic() - t0
            _log.error("Executable not found: '%s'", cmd[0])
            return CommandResult(command=cmd, returncode=-1, duration=dur, error=exc)
        except subprocess.TimeoutExpired as exc:
            dur = time.monotonic() - t0
            _log.error("Command timed out after %.1fs: %s", timeout, shlex.join(cmd))
            return CommandResult(
                command=cmd,
                returncode=-1,
                stderr="Process timed out.",
                duration=dur,
                error=exc,
            )
        except OSError as exc:
            dur = time.monotonic() - t0
            _log.error("OS error running '%s': %s", cmd[0], exc)
            return CommandResult(command=cmd, returncode=-1, duration=dur, error=exc)

        dur = time.monotonic() - t0
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()

        if stdout and self.log_stdout:
            _log.debug("stdout: %s", stdout[:2000])
        if stderr and self.log_stderr:
            lvl = _logging.WARNING if proc.returncode != 0 else _logging.DEBUG
            _log.log(lvl, "stderr: %s", stderr[:2000])

        lvl = _logging.DEBUG if proc.returncode == 0 else _logging.WARNING
        _log.log(lvl, "Finished (exit %d) in %.2fs: %s",
                 proc.returncode, dur, shlex.join(cmd))

        return CommandResult(
            command=cmd,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            duration=dur,
        )

    def _build_env(
        self,
        extra_env: Optional[Dict[str, str]],
    ) -> Optional[Dict[str, str]]:
        """Merge executor-level and per-call env vars on top of ``os.environ``."""
        if not self.env and not extra_env:
            return None   # fastest path: inherit as-is

        import os
        merged = dict(os.environ)
        if self.env:
            merged.update(self.env)
        if extra_env:
            merged.update(extra_env)
        return merged


# ---------------------------------------------------------------------------
# ThreadedExecutor
# ---------------------------------------------------------------------------

class ThreadedExecutor:
    """Run commands in a background thread to avoid blocking the Qt event loop.

    Callbacks are invoked from the background thread.  If you need to update
    Qt widgets inside the callback, emit a Qt signal rather than calling
    widget methods directly.

    Args:
        executor: The underlying synchronous :class:`Executor` to use.
                  If ``None``, a default ``Executor()`` is created.

    Example::

        def on_done(result: CommandResult) -> None:
            print("maketx finished:", result.success)

        tex = ThreadedExecutor(Executor(timeout=300))
        tex.run(["maketx", "input.exr", "-o", "out.tx"], on_complete=on_done)
        # Returns immediately; on_done called from background thread.
    """

    def __init__(self, executor: Optional[Executor] = None) -> None:
        self._executor = executor or Executor()
        self._threads: List[threading.Thread] = []

    def run(
        self,
        command: Sequence[str],
        on_complete: Optional[Callable[[CommandResult], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        daemon: bool = True,
    ) -> threading.Thread:
        """Spawn a thread to run *command*; call *on_complete* when done.

        Args:
            command:     Command and arguments.
            on_complete: Called with the :class:`CommandResult` on finish.
            on_error:    Called if a Python exception escapes the thread (rare).
            daemon:      Daemon threads don't block process exit.

        Returns:
            The started :class:`threading.Thread`.
        """
        def _target() -> None:
            try:
                result = self._executor.run(command)
                if on_complete:
                    on_complete(result)
            except Exception as exc:
                _log.exception("ThreadedExecutor: unexpected exception in thread")
                if on_error:
                    on_error(exc)

        t = threading.Thread(target=_target, daemon=daemon)
        self._threads.append(t)
        t.start()
        return t

    def wait_all(self, timeout: Optional[float] = None) -> None:
        """Block until all spawned threads finish (or *timeout* expires)."""
        for t in self._threads:
            t.join(timeout=timeout)
        # Prune completed threads.
        self._threads = [t for t in self._threads if t.is_alive()]

    @property
    def active_count(self) -> int:
        """Number of threads currently running."""
        self._threads = [t for t in self._threads if t.is_alive()]
        return len(self._threads)
