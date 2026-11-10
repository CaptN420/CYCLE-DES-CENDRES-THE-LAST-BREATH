"""Partie automatique de bout en bout du chapitre III (vraie boucle play())."""
from __future__ import annotations

import os
import sys
import tempfile
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import lore3, ui  # noqa: E402
from game.chapter3 import CHAMBER, Chapter3  # noqa: E402
from game.memory import Memory  # noqa: E402

KEYMAP = {
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
}
TO_KEY = {(0, -1): "w", (0, 1): "s", (-1, 0): "a", (1, 0): "d",
          (-1, -1): "y", (1, -1): "u", (-1, 1): "b", (1, 1): "n"}
FLIP = {"w": "s", "s": "w", "a": "d", "d": "a",
        "y": "n", "n": "y", "u": "b", "b": "u"}

MODALS = [
    ("LA DERNIÈRE PAGE", "3"),
    ("LE CRÉATEUR", "r"),
    ("LE PREMIER HÉROS", "o"),
    ("LE GARDIEN DU DERNIER MOT", "2"),
    ("MORT", "enter"),
    ("ELIA", "enter"),
    ("origin_000.txt", "enter"),
]


class AutoTerm:
    def __init__(self, god: bool = False):
        self.god = god
        self.ch: Chapter3 | None = None
        self.last: list[str] = []
        self.n = 0
        self.last_pos = (-1, -1)
        self.stuck = 0
        self.last_key = None

    def clear(self):
        pass

    def draw(self, lines):
        self.last = lines

    def getkey(self) -> str:
        self.n += 1
        if self.god and self.ch is not None and self.ch.player is not None and not self.ch.dead:
            self.ch.player.max_hp = max(self.ch.player.max_hp, 120)
            self.ch.player.hp = self.ch.player.max_hp
        if self.n % 500 == 0:
            ch = self.ch
            print(f"  [{self.n}] mode={ch.mode} sel={ch.selected} terr={ch.territory_key} "
                  f"pos={ch.player.x},{ch.player.y} hp={ch.player.hp} pages={ch.pages} "
                  f"cleared={sorted(ch.cleared)}")
        if self.n > (12000 if self.god else 1500):
            ch = self.ch
            pos = (ch.player.x, ch.player.y)
            feats = [(f.kind, f.x, f.y) for f in ch.dungeon.features
                     if max(abs(f.x - pos[0]), abs(f.y - pos[1])) <= 1]
            raise RuntimeError(f"boucle infinie mode={ch.mode} terr={ch.territory_key} "
                               f"pos={pos} pages={ch.pages} key={self.last_key!r} "
                               f"boss={ch.boss and ch.boss.alive} feats={feats}")
        text = ui.ANSI_RE.sub("", "\n".join(self.last))
        for marker, key in MODALS:
            if marker in text:
                return key
        ch = self.ch
        if ch.mode == "hub":
            if ch.pages >= 5:
                return "6" if ch.selected != CHAMBER else "e"
            nxt = next((i for i, t in enumerate(lore3.TERRITORIES) if t.key not in ch.cleared), None)
            if nxt is None:
                return "6"
            key = str(nxt + 1)
            return key if ch.selected != lore3.TERRITORIES[nxt].key else "e"
        p = ch.player
        if p.hp * 5 < p.max_hp * 3 and any("soin" in it.key for it in p.inventory):
            self.last_pos = (p.x, p.y)
            self.stuck = 0
            return "p"
        key = self._zone_key(ch)
        self.last_key = key
        if ch.invert_turns and key in FLIP:
            key = FLIP[key]
        adjacent = any(m.alive and not m.spared
                       and max(abs(m.x - p.x), abs(m.y - p.y)) == 1
                       for m in ch.monsters)
        if adjacent and ch.boss is not None and ch.boss.alive:
            if ch.charge_freeze > 0:
                self.last_pos = (p.x, p.y)
                return "f"
            if ch.charge_invoke > 0:
                self.last_pos = (p.x, p.y)
                return "v"
        if adjacent:
            self.stuck = 0
            self.last_pos = (p.x, p.y)
            return key
        if (ch.player.x, ch.player.y) == self.last_pos:
            self.stuck += 1
            if self.stuck > 2:
                self.stuck = 0
                return "r"
        else:
            self.stuck = 0
        self.last_pos = (ch.player.x, ch.player.y)
        return key

    def _zone_key(self, ch: Chapter3) -> str:
        p = ch.player
        if ch.territory_key == CHAMBER:
            book = next((f for f in ch.dungeon.features if f.kind == "book"), None)
            if book is None:
                return "e"
            if abs(book.x - p.x) + abs(book.y - p.y) <= 1:
                return "e"
            return self._step(ch, (book.x, book.y))
        target = None
        if ch.territory is not None and ch.territory.riddle and not ch.riddle_done:
            door = next((f for f in ch.dungeon.features if f.kind == "door"), None)
            if door is not None:
                if abs(door.x - p.x) + abs(door.y - p.y) <= 1:
                    return "e"
                return self._step(ch, (door.x, door.y))
        shrine = next((f for f in ch.dungeon.features
                       if f.kind == "shrine" and not f.data.get("used")), None)
        if shrine is not None and p.hp * 10 < p.max_hp * 7:
            if (shrine.x, shrine.y) == (p.x, p.y):
                return "e"
            return self._step(ch, (shrine.x, shrine.y))
        if ch.boss is not None and ch.boss.alive:
            target = (ch.boss.x, ch.boss.y)
        else:
            exit_feat = next((f for f in ch.dungeon.features if f.kind == "exit"), None)
            if exit_feat and (exit_feat.x, exit_feat.y) == (p.x, p.y):
                return "<"
            target = (exit_feat.x, exit_feat.y) if exit_feat else None
        if target is None:
            return "<"
        if target == (p.x, p.y):
            return "<"
        if abs(target[0] - p.x) + abs(target[1] - p.y) <= 1:
            dx = max(-1, min(1, target[0] - p.x))
            dy = max(-1, min(1, target[1] - p.y))
            return TO_KEY.get((dx, dy), "s")
        return self._step(ch, target)

    def _step(self, ch: Chapter3, target: tuple[int, int]) -> str:
        p = ch.player
        start = (p.x, p.y)
        if start == target:
            return "<"
        prev = {start: None}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            if cur == target:
                break
            for d, (dx, dy) in KEYMAP.items():
                nxt = (cur[0] + dx, cur[1] + dy)
                if nxt in prev or not ch.dungeon.walkable(*nxt):
                    continue
                prev[nxt] = (cur, d)
                queue.append(nxt)
        if target not in prev:
            return "r"
        node = target
        while prev[node] is not None and prev[node][0] != start:
            node = prev[node][0]
        if prev.get(node) is None:
            return "r"
        return prev[node][1]


def run_once(god: bool, seed: int) -> tuple[int, dict]:
    base = tempfile.mkdtemp()
    mem = Memory(os.path.join(base, "memoire.json"))
    mem.endings.append("sacrifice")
    mem.ch2["endings"].append("aube")
    mem.ch2["kael_ally"] = True
    mem.save()
    term = AutoTerm(god=god)
    ch = Chapter3(term, mem, seed=seed)
    term.ch = ch
    result = {"ok": False}
    try:
        ch.run()
    except RuntimeError as exc:
        result["error"] = str(exc)
        print(f"  arrêt : {exc}")
    result.update({
        "keys": term.n,
        "endings": list(mem.ch3["endings"]),
        "deaths": int(mem.ch3["deaths"]),
        "pages": int(mem.ch3["best_pages"]),
        "memories": len(mem.ch3["memories"]),
        "teaser": bool(mem.ch3["ch4_teaser"]),
    })
    result["ok"] = bool(result["endings"]) and result["teaser"]
    return term.n, result


def main():
    print("— sonde de difficulté : bot naïf —")
    _n, naive = run_once(False, 2024)
    print(f"  touches {naive['keys']} · fins {naive['endings']} · morts {naive['deaths']} "
          f"· pages max {naive['pages']}")

    print("\n— vérification d'intégration : boucle complète (PV maintenus) —")
    _n, god = run_once(True, 7)
    print(f"  touches {god['keys']} · fins {god['endings']} · pages max {god['pages']} "
          f"· souvenirs {god['memories']}/7 · épilogue {god['teaser']}")
    print("PARTIE COMPLÈTE :", "OK" if god["ok"] else "ÉCHEC")
    return 0 if god["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())