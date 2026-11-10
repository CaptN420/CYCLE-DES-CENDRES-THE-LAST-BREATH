"""Aperçus texte du Chapitre II (sans ANSI)."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import chapter2, lore2, memory as memmod, ui  # noqa: E402

OUT = os.path.join(ROOT, "tests", "apercus2.txt")


class FakeTerm:
    def __init__(self, keys=()):
        self.keys = list(keys)
        self.frames = []

    def draw(self, lines):
        self.frames.append(list(lines))

    def clear(self):
        pass

    def hide_cursor(self):
        pass

    def show_cursor(self):
        pass

    def getkey(self):
        return self.keys.pop(0) if self.keys else "esc"


def plain(lines):
    return "\n".join(ui.ANSI_RE.sub("", line) for line in lines)


def main():
    path = os.path.join(ROOT, "tests", "_apercu2.json")
    if os.path.exists(path):
        os.remove(path)
    mem = memmod.Memory(path)
    mem.reset()
    mem.record_ending("sacrifice")
    term = FakeTerm()
    g = chapter2.Chapter2(term, mem, seed=5)
    g.new_run()
    chunks = []

    term.keys = ["esc"]
    g.legacy_screen()
    chunks.append("=== HÉRITAGE (fin du chapitre I : sacrifice) ===\n" + plain(term.frames[-1]))

    chunks.append("=== CARTE DU MONDE ===\n" + plain(g.frame()))
    g.cleared = {"vhaldor", "foret"}
    g.fragments = 3; g.player.fragments = 3
    g.selected = "skaar"
    g.log("Le fragment de la Forêt des Murmures est à toi. (3/7)", ui.YELLOW)
    chunks.append("=== CARTE DU MONDE (2 régions purgées) ===\n" + plain(g.frame()))

    g.cleared = set()
    g.enter_region("vhaldor")
    g.player.x, g.player.y = g.dungeon.start
    g.update_fov()
    chunks.append("=== RÉGION : VHALDOR ===\n" + plain(g.frame()))

    g.enter_region("foret")
    g.update_fov()
    chunks.append("=== RÉGION : FORÊT DES MURMURES ===\n" + plain(g.frame()))

    term.keys = ["esc"]
    g.open_inventory()
    chunks.append("=== SAC (chapitre II) ===\n" + plain(term.frames[-1]))

    g.fragments = 7
    g.knowledge = 4
    g.enter_origin()
    g.update_fov()
    chunks.append("=== LE CŒUR DE L'ORIGINE ===\n" + plain(g.frame()))

    term.keys = ["esc"]
    g.ending_choice()
    chunks.append("=== CHOIX FINAL ===\n" + plain(term.frames[-1]))

    term.keys = ["enter"]
    g.ending_screen("aube")
    chunks.append("=== FIN : LA DERNIÈRE AUBE ===\n" + plain(term.frames[-1]))

    term.keys = ["enter"]
    g.final_scene()
    chunks.append("=== SCÈNE FINALE ===\n" + plain(term.frames[-1]))

    g.player.hp = 0
    g.depth = None
    g.region = lore2.REGION_BY_KEY["vhaldor"]
    g.dead_cause = "La Mère des Racines"
    g.fragments = 3; g.player.fragments = 3
    mem.ch2["deaths"] = 5
    term.keys = ["q"]
    g.death_screen()
    chunks.append("=== MORT (palier 5) ===\n" + plain(term.frames[-1]))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(chunks))
    print("écrit:", OUT)


if __name__ == "__main__":
    main()