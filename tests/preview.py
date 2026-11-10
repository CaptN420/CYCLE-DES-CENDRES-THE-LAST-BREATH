"""Génère des aperçus texte du jeu (sans ANSI) pour vérification visuelle."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import entities as ent, game as gm, items, ui, memory as memmod  # noqa: E402

OUT = os.path.join(ROOT, "tests", "apercus.txt")


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
    mem = memmod.Memory(os.path.join(ROOT, "tests", "_apercu.json"))
    mem.reset()
    term = FakeTerm()
    g = gm.Game(term, mem, seed=4)
    g.player = ent.Player(mem)
    chunks = []

    term.keys = ["esc"]
    g.title_screen()
    chunks.append("=== ÉCRAN TITRE ===\n" + plain(term.frames[-1]))

    g.new_run()
    g.load_floor(3)
    g.update_fov()
    chunks.append("=== ÉTAGE 3 (cité engloutie) ===\n" + plain(g.frame()))

    # aperçu de l'inventaire
    g.player.add_item(items.make_potion(g.rng))
    g.player.add_item(items.make_scroll(g.rng))
    term.keys = ["esc"]
    g.open_inventory()
    chunks.append("=== INVENTAIRE ===\n" + plain(term.frames[-1]))

    # aperçu de l'écran de mort
    g.player.kills = 7
    g.player.gold = 42
    g.depth = 5
    g.die("Démon mineur")
    term.keys = ["q"]
    g.death_screen()
    chunks.append("=== MORT ===\n" + plain(term.frames[-1]))

    # aperçu de fin
    g.depth = 7
    g.ending = "secret"
    term.keys = ["q"]
    g.ending_screen("secret")
    chunks.append("=== FIN SECRÈTE ===\n" + plain(term.frames[-1]))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(chunks))
    print("écrit:", OUT)


if __name__ == "__main__":
    main()
