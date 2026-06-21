"""
lh_houdini_pipeline.core.path
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Path normalisation, template substitution, and context-aware resolution.

This module provides three building blocks:

    normalize()    -- convert any path to a consistent forward-slash string
    PathTemplate   -- immutable template with ``{variable}`` placeholders
    PathResolver   -- context dict that resolves templates against it

Design principles
-----------------
* Pure Python -- no ``hou`` imports; fully testable outside Houdini.
* ``pathlib.Path`` is used internally; callers receive ``str`` by default
  because Houdini and most pipeline tools prefer plain strings.
* Forward-slash output even on Windows (USD / Houdini convention).
* Templates follow Python's ``str.format_map`` syntax, so standard
  format specs work (e.g. ``{version:03d}``).
* ``PathTemplate`` is immutable; ``format_partial()`` returns a *new*
  template, enabling incremental resolution across pipeline layers.
* ``PathResolver.with_overrides()`` returns a *copy*, preventing
  accidental mutation of shared show-level resolvers.

Example
-------
::

    from lh_houdini_pipeline.core.path import PathResolver

    show = PathResolver(root="/jobs", project="darkStar")
    shot = show.with_overrides(shot="sh0100", department="fx")

    hip = shot.resolve(
        "{root}/{project}/houdini/{shot}/work/{department}_v{version:03d}.hip",
        version=3,
    )
    # "/jobs/darkStar/houdini/sh0100/work/fx_v003.hip"
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Module-level utilities
# ---------------------------------------------------------------------------

def normalize(path: PathLike) -> str:
    """Return *path* as a forward-slash string, collapsing redundant separators.

    This is the canonical path representation used throughout the pipeline.
    Drive letters are preserved on Windows (``C:/jobs/...``).

    Trailing slashes are preserved -- they are meaningful in pipeline path
    templates (e.g. directory roots differ from file paths).

    Args:
        path: A ``str`` or ``pathlib.Path`` to normalise.

    Returns:
        A normalised, forward-slash path string.

    Examples:
        >>> normalize(r"C:\\\\jobs\\\\darkStar\\\\shots")
        'C:/jobs/darkStar/shots'
        >>> normalize("/jobs/darkStar/houdini/")
        '/jobs/darkStar/houdini/'
    """
    raw = str(path)
    # pathlib strips trailing separators; preserve them.
    had_trailing = raw.endswith("/") or raw.endswith("\\")
    result = Path(path).as_posix()
    if had_trailing and not result.endswith("/"):
        result += "/"
    return result


def ensure_dir(path: PathLike) -> Path:
    """Create *path* as a directory (and all parents) if it does not exist.

    Equivalent to ``mkdir -p``.

    Args:
        path: Directory to create.

    Returns:
        ``pathlib.Path`` pointing at *path*.

    Raises:
        OSError: If the directory cannot be created (e.g. permission denied).
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_parent(path: PathLike) -> Path:
    """Create the *parent* directory of *path* if it does not exist.

    Use when you have a file path and want its containing folder ready before
    writing.

    Args:
        path: A file path whose parent directory should be created.

    Returns:
        ``pathlib.Path`` pointing at *path* (the file, not the directory).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------------------
# Internal template substitution
# ---------------------------------------------------------------------------

# Matches {name} and {name:spec} tokens.
_TMPL_RE = re.compile(r"\{(\w+)(?::([^}]*))?\}")


def _substitute(template: str, context: Dict[str, Any]) -> str:
    """Replace ``{name}`` and ``{name:spec}`` tokens via regex callback.

    This is intentionally *not* using ``str.format_map`` so that the
    resolver stays free of any SQL-injection surface -- the only input
    here is a *path* template, never a SQL string.

    Args:
        template: Path template string containing ``{variable}`` tokens.
        context:  Mapping of variable names to their values.

    Returns:
        The substituted string with all tokens replaced.

    Raises:
        KeyError: If a token in *template* has no entry in *context*.
    """
    missing: List[str] = []

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        key = match.group(1)
        spec = match.group(2)
        if key not in context:
            missing.append(key)
            return match.group(0)   # leave token in place; report below
        value = context[key]
        return format(value, spec) if spec else str(value)

    result = _TMPL_RE.sub(_replace, template)

    if missing:
        raise KeyError(missing[0])

    return result


# ---------------------------------------------------------------------------
# PathTemplate
# ---------------------------------------------------------------------------

class PathTemplate:
    """An immutable path string with ``{variable}`` placeholders.

    Provides pipeline-specific conveniences on top of simple token substitution:

    * :py:meth:`format` -- fully resolve all variables; return normalised str
    * :py:meth:`format_partial` -- resolve a subset; return a new PathTemplate
    * :py:meth:`missing_variables` -- which vars are absent from a given context
    * :py:meth:`is_satisfied_by` -- True if context covers all variables

    Standard Python format-spec mini-language is honoured inside placeholders
    (e.g. ``{version:03d}`` with ``version=4`` → ``"004"``).

    The template string is stored as-is.  Normalisation (forward slashes) is
    applied only on the *resolved* output of :py:meth:`format`.

    Args:
        template: A path string with zero or more ``{name}`` placeholders.

    Example:
        >>> t = PathTemplate("{root}/{project}/shots/{shot}/work")
        >>> t.variables
        ['root', 'project', 'shot']
        >>> t.format(root="/jobs", project="darkStar", shot="sh0100")
        '/jobs/darkStar/shots/sh0100/work'
    """

    def __init__(self, template: str) -> None:
        self._template: str = template
        # Extract bare variable names (before any ':' spec) for introspection.
        self._raw_vars: List[str] = _TMPL_RE.findall(template)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def template(self) -> str:
        """The raw template string (unchanged)."""
        return self._template

    @property
    def variables(self) -> List[str]:
        """Ordered, deduplicated list of variable names in this template."""
        seen: set = set()
        # _raw_vars is a list of (name, spec) tuples from the regex groups
        return [
            name
            for (name, _spec) in self._raw_vars
            if not (name in seen or seen.add(name))
        ]

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def format(self, **kwargs: Any) -> str:
        """Fully resolve the template and return a normalised path string.

        Args:
            **kwargs: Values for each placeholder.  Standard format mini-language
                is honoured (e.g. ``version=4`` with ``{version:03d}`` → ``"004"``).

        Returns:
            A forward-slash path string with all placeholders substituted.

        Raises:
            KeyError: If one or more required variables are absent from *kwargs*.

        Example:
            >>> PathTemplate("{root}/{project}/v{version:03d}").format(
            ...     root="/jobs", project="darkStar", version=4
            ... )
            '/jobs/darkStar/v004'
        """
        try:
            resolved = _substitute(self._template, kwargs)
        except KeyError as exc:
            raise KeyError(
                f"PathTemplate missing variable {exc}. "
                f"Required: {self.variables}. "
                f"Provided: {sorted(kwargs.keys())}."
            ) from exc
        return normalize(resolved)

    def format_partial(self, **kwargs: Any) -> "PathTemplate":
        """Resolve *only* the supplied variables; leave the rest unchanged.

        Returns a **new** :class:`PathTemplate` -- the original is never mutated.
        Useful for multi-layer resolution: resolve ``{root}`` at studio init,
        ``{shot}`` at session open, ``{version}`` at save time.

        Args:
            **kwargs: Subset of variable values to substitute now.

        Returns:
            New :class:`PathTemplate` with remaining variables still present.

        Example:
            >>> t = PathTemplate("{root}/{project}/{shot}/work")
            >>> t2 = t.format_partial(root="/jobs", project="darkStar")
            >>> t2.template
            '/jobs/darkStar/{shot}/work'
            >>> t2.format(shot="sh0100")
            '/jobs/darkStar/sh0100/work'
        """
        def _safe_replace(match: re.Match) -> str:  # type: ignore[type-arg]
            key = match.group(1)
            spec = match.group(2)
            if key not in kwargs:
                return match.group(0)   # keep token unchanged
            value = kwargs[key]
            return format(value, spec) if spec else str(value)

        partial = _TMPL_RE.sub(_safe_replace, self._template)
        return PathTemplate(partial)

    def missing_variables(self, context: Dict[str, Any]) -> List[str]:
        """Variable names present in the template but absent from *context*.

        Args:
            context: A mapping of variable names to values.

        Returns:
            Ordered list of missing variable names.
        """
        return [v for v in self.variables if v not in context]

    def is_satisfied_by(self, context: Dict[str, Any]) -> bool:
        """Return ``True`` if *context* supplies all variables in the template."""
        return len(self.missing_variables(context)) == 0

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"PathTemplate({self._template!r})"

    def __str__(self) -> str:
        return self._template

    def __eq__(self, other: object) -> bool:
        return isinstance(other, PathTemplate) and self._template == other._template

    def __hash__(self) -> int:
        return hash(self._template)


# ---------------------------------------------------------------------------
# PathResolver
# ---------------------------------------------------------------------------

class PathResolver:
    """Context-aware resolver that fills :class:`PathTemplate` placeholders.

    Holds a *context* dictionary of named variables (project root, shot name,
    department, etc.) and resolves path templates against it.  Per-call
    overrides can supplement the context without mutating it.

    Typical usage -- one resolver per Houdini session::

        show = PathResolver(root="/jobs", project="darkStar")

        # Derive a shot-level resolver without mutating the show resolver.
        shot = show.with_overrides(shot="sh0100", department="fx")

        hip = shot.resolve(
            "{root}/{project}/houdini/{shot}/work/{department}_v{version:03d}.hip",
            version=3,
        )
        # "/jobs/darkStar/houdini/sh0100/work/fx_v003.hip"

    Environment-variable expansion (``$JOB``, ``${JOB}``) is performed
    **before** template substitution, allowing site roots to be provided via
    the environment and composed with project-level variables.

    Args:
        **context: Initial variable bindings.
    """

    def __init__(self, **context: Any) -> None:
        self._context: Dict[str, Any] = {}
        self.update(**context)

    # ------------------------------------------------------------------
    # Context management
    # ------------------------------------------------------------------

    def update(self, **context: Any) -> None:
        """Merge new variable bindings into this resolver in-place.

        Args:
            **context: New or updated variable bindings.
        """
        self._context.update(context)

    def with_overrides(self, **overrides: Any) -> "PathResolver":
        """Return a *copy* of this resolver with additional variable bindings.

        The original resolver is never modified.  Useful for deriving
        shot-level resolvers from a show-level one while keeping the
        show resolver reusable.

        Args:
            **overrides: Variables to add or override in the copy.

        Returns:
            A new :class:`PathResolver` instance.
        """
        copy = PathResolver(**self._context)
        copy.update(**overrides)
        return copy

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value of a single context variable, or *default*."""
        return self._context.get(key, default)

    @property
    def context(self) -> Dict[str, Any]:
        """A snapshot (shallow copy) of the current context dictionary."""
        return dict(self._context)

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        template: Union[str, PathTemplate],
        **overrides: Any,
    ) -> str:
        """Resolve *template* to a normalised path string.

        Processing order:

        1. Expand environment variables in the raw string
           (``$JOB`` becomes the value of the JOB env var).
        2. Merge stored context with per-call *overrides*
           (overrides take priority).
        3. Substitute all ``{variable}`` tokens.
        4. Normalise result to forward slashes.

        Args:
            template: A path template string or :class:`PathTemplate`.
            **overrides: Temporary variables that supplement (or override) the
                stored context for this single call only.

        Returns:
            Normalised, fully resolved path string.

        Raises:
            KeyError: If the template contains variables absent from both
                the stored context and *overrides*.

        Example:
            >>> r = PathResolver(root="/jobs", project="darkStar")
            >>> r.resolve("{root}/{project}/v{version:03d}", version=2)
            '/jobs/darkStar/v002'
        """
        expanded = os.path.expandvars(str(template))
        tmpl = PathTemplate(expanded)
        ctx = {**self._context, **overrides}
        return tmpl.format(**ctx)

    def resolve_path(
        self,
        template: Union[str, PathTemplate],
        **overrides: Any,
    ) -> Path:
        """Like :py:meth:`resolve` but returns a :class:`pathlib.Path`.

        Useful when you need ``.exists()``, ``.stat()``, etc. immediately.
        """
        return Path(self.resolve(template, **overrides))

    def try_resolve(
        self,
        template: Union[str, PathTemplate],
        default: Optional[str] = None,
        **overrides: Any,
    ) -> Optional[str]:
        """Like :py:meth:`resolve` but returns *default* instead of raising.

        Args:
            template: Path template to resolve.
            default:  Returned when resolution fails.  Defaults to ``None``.
            **overrides: Per-call variable overrides.

        Returns:
            Resolved path string, or *default* on any failure.
        """
        try:
            return self.resolve(template, **overrides)
        except (KeyError, ValueError):
            return default

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"PathResolver(context={sorted(self._context.keys())})"
