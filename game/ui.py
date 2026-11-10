"""Terminal utilities: ANSI colours, frame drawing, keyboard input (Windows + POSIX)."""
from __future__ import annotations

import os
import re
import sys

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
HOME = "\x1b[H"
CLEAR = "\x1b[2J"

# 256-colour palette entries used across the game
WHITE = 255
GREY = 250
MIDGREY = 245
DARKGREY = 240
VOID = 236
RED = 160
BRIGHTRED = 196
ORANGE = 208
GOLD = 220
YELLOW = 226
GREEN = 78
DARKGREEN = 34
CYAN = 51
BLUE = 33
PURPLE = 141
MAGENTA = 201
BONE = 253
BROWN = 137


def paint(text: str, colour: int | None = None, bold: bool = False, dim: bool = False) -> str:
    """Wrap text in ANSI escapes. `colour` is a 256-colour index."""
    prefix = ""
    if bold:
        prefix += BOLD
    if dim:
        prefix += DIM
    if colour is not None:
        prefix += f"\x1b[38;5;{colour}m"
    if not prefix:
        return text
    return f"{prefix}{text}{RESET}"


def vlen(text: str) -> int:
    """Visible length, ignoring ANSI escapes."""
    return len(ANSI_RE.sub("", text))


def pad(text: str, width: int, align: str = "left") -> str:
    """Pad to a visible width (truncating if too long)."""
    plain = ANSI_RE.sub("", text)
    if len(plain) > width:
        return truncate_colored(text, width)
    gap = width - len(plain)
    if align == "right":
        return " " * gap + text
    if align == "center":
        left = gap // 2
        return " " * left + text + " " * (gap - left)
    return text + " " * gap


def truncate_colored(text: str, width: int) -> str:
    """Truncate an ANSI-coloured string to `width` visible chars, keeping escapes."""
    out = []
    visible = 0
    i = 0
    while i < len(text) and visible < width:
        if text[i] == "\x1b":
            m = ANSI_RE.match(text, i)
            if m:
                out.append(m.group(0))
                i = m.end()
                continue
        out.append(text[i])
        visible += 1
        i += 1
    out.append(RESET)
    return "".join(out)


def wrap(text: str, width: int) -> list[str]:
    """Naive word wrap preserving whole words (good enough for our ASCII frames)."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= width:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


class Terminal:
    """Full-screen terminal with a minimal key reader."""

    def __init__(self) -> None:
        self.windows = os.name == "nt"
        self._old_out = None
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        self._enable_vt()

    def _enable_vt(self) -> None:
        if not self.windows:
            return
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                # ENABLE_VIRTUAL_TERMINAL_PROCESSING | DISABLE_NEWLINE_AUTO_RETURN
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            # give the window a sane size for our 79x29 frame
            try:
                kernel32.SetConsoleTitleW("CYCLE DES CENDRES")
            except Exception:
                pass
        except Exception:
            pass

    # ---------------------------------------------------------------- output
    def draw(self, lines: list[str]) -> None:
        """Draw a full frame without flicker (home cursor, rewrite lines)."""
        buf = [HOME]
        for line in lines:
            buf.append(line)
            buf.append("\x1b[K\r\n")
        sys.stdout.write("".join(buf))
        sys.stdout.flush()

    def hide_cursor(self) -> None:
        sys.stdout.write(HIDE_CURSOR)
        sys.stdout.flush()

    def show_cursor(self) -> None:
        sys.stdout.write(SHOW_CURSOR + RESET)
        sys.stdout.flush()

    def clear(self) -> None:
        sys.stdout.write(CLEAR + HOME)
        sys.stdout.flush()

    # ----------------------------------------------------------------- input
    def getkey(self) -> str:
        """Blocking single keypress. Arrows/function keys become names."""
        if self.windows:
            return self._getkey_windows()
        return self._getkey_posix()

    def _getkey_windows(self) -> str:
        import msvcrt

        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            code = msvcrt.getwch()
            return {
                "H": "UP",
                "P": "DOWN",
                "K": "LEFT",
                "M": "RIGHT",
                "G": "HOME",
                "O": "END",
                "I": "PGUP",
                "Q": "PGDN",
                "S": "DELETE",
                "\x1b": "ESC",
            }.get(code, "")
        if ch == "\r":
            return "ENTER"
        if ch == "\x1b":
            return "ESC"
        if ch in ("\x08", "\x7f"):
            return "BACKSPACE"
        if ch == " ":
            return "SPACE"
        return ch

    def _getkey_posix(self) -> str:
        if self._old_out is None:
            self._old_out = True
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                seq = sys.stdin.read(2)
                return {"[A": "UP", "[B": "DOWN", "[C": "RIGHT", "[D": "LEFT"}.get(seq, "ESC")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if ch == "\r":
            return "ENTER"
        if ch == "\x7f":
            return "BACKSPACE"
        if ch == " ":
            return "SPACE"
        return ch


def box_top(inner: int, title: str = "") -> str:
    return "╔" + "═" * inner + "╗"


def box_bottom(inner: int) -> str:
    return "╚" + "═" * inner + "╝"


def box_sep(inner: int) -> str:
    return "╠" + "═" * inner + "╣"
