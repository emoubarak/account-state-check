"""Deprecated name. jev-check was renamed account-state-check; this package only forwards to
`account_state_check`, so `from jevcheck import Check, result, ...` in existing checks files
keeps working. New code: `from account_state_check import ...`."""

import warnings

from account_state_check import *  # noqa: F401,F403
from account_state_check import __all__, __version__  # noqa: F401

warnings.warn(
    "the `jevcheck` Python package is now `account_state_check`; update your import "
    "(`from account_state_check import Check, result, ...`). The old name will be removed in a future major version.",
    DeprecationWarning,
    stacklevel=2,
)
