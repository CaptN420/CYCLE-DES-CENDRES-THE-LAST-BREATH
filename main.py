"""CYCLE DES CENDRES — point d'entrée."""
from __future__ import annotations

import os
import sys
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from game.chapter2 import Chapter2  # noqa: E402
from game.chapter3 import Chapter3  # noqa: E402
from game.game import Game          # noqa: E402
from game.memory import Memory      # noqa: E402
from game.menu import main_menu     # noqa: E402
from game.ui import Terminal        # noqa: E402


def main() -> int:
    term = Terminal()
    term.hide_cursor()
    mem = Memory()
    try:
        while True:
            choice = main_menu(term, mem)
            if choice is None:
                break
            if choice == "ch1":
                Game(term, mem).run()
            elif choice == "ch2":
                Chapter2(term, mem).run()
            else:
                Chapter3(term, mem).run()
    except KeyboardInterrupt:
        pass
    except Exception:
        term.show_cursor()
        term.clear()
        traceback.print_exc()
        try:
            input("\nUne erreur est survenue. Appuie sur Entrée pour fermer.")
        except Exception:
            pass
        return 1
    finally:
        term.show_cursor()
        term.clear()

    print()
    print("  Le monde se referme sur ses morts. Il t'attendra.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
