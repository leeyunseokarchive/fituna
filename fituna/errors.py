"""fituna.errors
================

Re-exports the :class:`FiTunaError` hierarchy from :mod:`fituna.config`.

The exceptions are defined once, in ``config.py``, alongside the rest of the
interface contract (single source of truth for cross-module types). This
module exists only so ``from fituna.errors import ...`` reads naturally from
call sites that only care about error handling, not the data model.
"""

from fituna.config import (
    BinaryNotFoundError,
    FiTunaError,
    ModelConversionError,
    NoFeasibleConfigError,
)

__all__ = [
    "FiTunaError",
    "BinaryNotFoundError",
    "ModelConversionError",
    "NoFeasibleConfigError",
]
