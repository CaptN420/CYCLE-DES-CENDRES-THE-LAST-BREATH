"""Aperçus texte du chapitre III (sans ANSI) pour contrôle visuel."""
from __future__ import annotations

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import lore3, ui  # noqa: E402
from game.chapter3 import CHAMBER, Chapter3  # noqa: E402
from game.memory import Memory  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apercus3.txt")


class FakeTerm:
    def __init__(self, keys=None):
        self.keys = list(keys or [])
        self.last = []

    def clear(self):
        pass

    def draw(self, lines):
        self.last = lines

    def getkey(self):
        return self.keys.pop(0) if self.keys else "esc"


def plain(lines):
    return "\n".join(ui.ANSI_RE.sub("", line).rstrip() for line in lines)


def main():
    mem = Memory(os.path.join(tempfile.mkdtemp(), "memoire.json"))
    mem.endings.append("sacrifice")
    mem.ch2["endings"].append("aube")
    mem.ch2["kael_ally"] = True
    term = FakeTerm()
    ch = Chapter3(term, mem, seed=99)
    ch.new_run()
    blocks = []

    blocks.append(("== HUB — L'INTERVALLE ==", ch.frame()))
    for t in lore3.TERRITORIES:
        ch.enter_territory(t.key)
        ch.update_fov()
        blocks.append((f"== {t.name} ==", ch.frame()))
        ch.leave_territory()

    ch.mem.ch3["deaths"] = 3
    ch.enter_territory("cite")
    ch.player.hp = 1
    ch.die("Un Toi, version dieu")
    term.keys = ["enter"]
    ch.death_screen()
    blocks.append(("== MORT ==", term.last))

    ch.pages = 5
    ch.enter_chamber()
    blocks.append(("== CHAMBRE DE L'AUTEUR ==", ch.frame()))

    for line in lore3.ENDINGS["impossible"]["lines"]:
        pass
    ch.ending = "impossible"
    ch.ending_screen("impossible")
    blocks.append(("== FIN SECRÈTE ==", term.last))

    ch.final_scene()
    blocks.append(("== ÉPILOGUE ==", term.last))

    with open(OUT, "w", encoding="utf-8") as fh:
        for title, lines in blocks:
            fh.write(title + "\n")
            fh.write(plain(lines) + "\n\n")
    print(f"{len(blocks)} aperçus écrits dans {OUT}")


if __name__ == "__main__":
    main()