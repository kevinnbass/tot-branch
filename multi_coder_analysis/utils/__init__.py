"""Utility sub-package.

This package exposes helper functions that are shared across the codebase.

Public re-exports
-----------------
archive_resolved
    Stream concluded :class:`~multi_coder_analysis.models.HopContext` objects to a
    worker-local JSON Lines archive file.  The function lives in
    :pymod:`multi_coder_analysis.utils.archiver` but is re-exported here for
    convenience so callers can simply write::

        from multi_coder_analysis.utils import archive_resolved

    instead of remembering the full sub-module path.
"""

from .archiver import archive_resolved  # noqa: F401 