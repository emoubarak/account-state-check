"""Deprecated `jevcheck` command (the pre-rename name): prints a notice, runs `account-state-check`."""

import sys


def main(argv=None):
    print("warning: `jevcheck` is deprecated, it is now `account-state-check` (same arguments). "
          "This alias will be removed in a future major version.", file=sys.stderr)
    from .cli import main as real_main
    return real_main(argv)
