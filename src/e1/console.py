"""
Console output helper for E1 (UI printing with quiet mode).
"""

from dataclasses import dataclass


@dataclass
class ConsolePrinter:
    """
    Console printer with optional quiet mode.

    When quiet=True, all output is suppressed.
    """

    quiet: bool = False

    def write(self, message: str = "", end: str = "\n", flush: bool = False) -> None:
        if self.quiet:
            return
        print(message, end=end, flush=flush)
