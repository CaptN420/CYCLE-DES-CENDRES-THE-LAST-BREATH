"""Tests réels du Chapitre II (py -3 tests/test_chapter2.py)."""
from __future__ import annotations

import os
import sys
import tempfile
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import chapter2, entities as ent, items, lore2, memory as memmod, ui  # noqa: E402

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


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
        if not self.keys:
            raise RuntimeError("plus de touches dans le scénario")
        return self.keys.pop(0)


def temp_memory():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    os.remove(path)
    return memmod.Memory(path)


def new_game(keys=(), seed=7, ending=None):
    mem = temp_memory()
    if ending:
        mem.record_ending(ending)
    term = FakeTerm(keys)
    g = chapter2.Chapter2(term, mem, seed=seed)
    g.new_run()
    return g, mem, term


@check("cadre 79x28 : monde + 6 régions + origine")
def test_geometry():
    g, mem, term = new_game()
    world = g.frame()
    assert len(world) == 28, len(world)
    for i, line in enumerate(world):
        assert ui.vlen(line) == 79, (i, ui.vlen(line))
    for region in lore2.REGIONS:
        g.enter_region(region.key)
        frame = g.frame()
        assert len(frame) == 28
        for i, line in enumerate(frame):
            assert ui.vlen(line) == 79, (region.key, i, ui.vlen(line))


@check("région : boss, stèle, sortie, PNJ présents et accessibles")
def test_region_contents():
    g, mem, term = new_game()
    for region in lore2.REGIONS:
        g.cleared.clear()
        g.enter_region(region.key)
        d = g.dungeon
        kinds = {f.kind for f in d.features}
        assert "exit" in kinds and "stele" in kinds, (region.key, kinds)
        assert "npc" in kinds, (region.key, kinds)
        assert g.boss is not None and g.boss.alive, region.key
        # le boss est dans une salle, sur une case marchable
        assert d.walkable(g.boss.x, g.boss.y), region.key
        # la sortie est sur la case de départ
        assert d.feature_at(g.player.x, g.player.y).kind == "exit"


@check("boss tué : fragment, souvenirs, région purgée")
def test_boss_reward():
    g, mem, term = new_game()
    g.enter_region("vhaldor")
    boss = g.boss
    boss.hp = 1
    g.player_attack(boss)
    assert not boss.alive
    assert g.fragments == 2, g.fragments
    assert "vhaldor" in g.cleared
    assert mem.ch2["souvenirs"] >= 3
    assert mem.ch2["knowledge"] >= 1
    # la région purgée ne régénère pas de boss
    g.enter_region("vhaldor")
    assert g.boss is None
    assert any("purger" in msg.lower() or "purgée" in msg for msg, _ in g.messages)


@check("stèle : +1 savoir, persistant sur disque")
def test_stele():
    g, mem, term = new_game()
    g.enter_region("foret")
    stele = next(f for f in g.dungeon.features if f.kind == "stele")
    before = g.knowledge
    g.player.x, g.player.y = stele.x, stele.y
    g.read_stele(stele)
    assert g.knowledge == before + 1
    again = memmod.Memory(mem.path)
    assert again.ch2["knowledge"] == g.knowledge
    g.read_stele(stele)  # relire ne donne rien
    assert g.knowledge == before + 1


@check("PNJ Morvan : commerce contre souvenirs")
def test_morvan():
    g, mem, term = new_game(keys=["a"], seed=11)
    g.enter_region("skaar")
    g.souvenirs = 5
    npc = next(f for f in g.dungeon.features if f.kind == "npc")
    g.player.x, g.player.y = npc.x, npc.y
    inv_before = len(g.player.inventory)
    g.interact()
    assert g.souvenirs == 2, g.souvenirs
    assert len(g.player.inventory) > inv_before


@check("Kael : duel puis allié persistant")
def test_kael_duel():
    g, mem, term = new_game(keys=["c"], seed=13)
    g.enter_region("vhaldor")
    npc = next(f for f in g.dungeon.features if f.kind == "npc")
    g.player.x, g.player.y = npc.x, npc.y
    g.interact()
    assert getattr(g, "special_kael", None) is not None
    kael = g.special_kael
    kael.hp = 1
    g.player_attack(kael)
    assert g.kael_ally
    assert mem.ch2["kael_ally"] is True
    reloaded = memmod.Memory(mem.path)
    assert reloaded.ch2["kael_ally"] is True
    g2, _, _ = new_game(seed=17)
    g2.mem = mem
    g2.new_run()
    assert g2.kael_ally


@check("mort : enregistrée, monde modifié (palier 1 puis 3)")
def test_death_tiers():
    g, mem, term = new_game()
    g.enter_region("vhaldor")
    g.player.hp = 1
    g.die("Test de mortalité")
    assert g.dead
    assert mem.ch2["deaths"] == 1
    assert mem.ch2["death_log"][0]["weapon"] == g.player.weapon.name
    # nouvelle partie : les échos apparaissent
    g2, _, _ = new_game(seed=19)
    g2.mem = mem
    g2.new_run()
    g2.enter_region("foret")
    names = [m.name for m in g2.monsters]
    assert any("Souffle errant" in n for n in names), names


@check("6 régions purgées + origine : boss final puis 5 fins")
def test_full_route_and_endings():
    for choice, ending in (("1", "dernier_dieu"), ("2", "silence"), ("3", "aube"),
                           ("4", "sacrifice_eternel")):
        g, mem, term = new_game(keys=[choice, "enter"], seed=23)
        g.fragments = 7
        g.knowledge = 4
        g.enter_origin()
        boss = g.boss
        assert boss.name.startswith("LE PREMIER SILENCE")
        boss.hp = 1
        g.player_attack(boss)
        heart = next(f for f in g.dungeon.features if f.kind == "heart")
        g.player.x, g.player.y = heart.x, heart.y
        g.ending_choice()
        assert g.ending == ending, (choice, g.ending)
        assert ending in mem.ch2["endings"]


@check("Vérité Interdite verrouillée sans savoir, ouverte à 4")
def test_truth_gate():
    g, mem, term = new_game(keys=["5", "1", "enter"], seed=29)
    g.fragments = 7
    g.knowledge = 2
    g.enter_origin()
    g.boss.hp = 1
    g.player_attack(g.boss)
    heart = next(f for f in g.dungeon.features if f.kind == "heart")
    g.player.x, g.player.y = heart.x, heart.y
    g.ending_choice()
    assert g.ending == "dernier_dieu", g.ending   # 5 refusé -> retombe sur 1

    g2, mem2, term2 = new_game(keys=["5", "enter"], seed=31)
    g2.fragments = 7
    g2.knowledge = 4
    g2.enter_origin()
    g2.boss.hp = 1
    g2.player_attack(g2.boss)
    heart = next(f for f in g2.dungeon.features if f.kind == "heart")
    g2.player.x, g2.player.y = heart.x, heart.y
    g2.ending_choice()
    assert g2.ending == "verite_interdite", g2.ending


@check("scène finale : souvenir LE CRÉATEUR débloqué")
def test_final_scene():
    g, mem, term = new_game(keys=["enter", "enter"], seed=37)
    g.final_scene()
    assert mem.ch2.get("ch3_teaser") is True
    reloaded = memmod.Memory(mem.path)
    assert reloaded.ch2.get("ch3_teaser") is True


@check("héritage du Chapitre I appliqué au départ")
def test_legacy():
    g, mem, term = new_game(ending="sacrifice")
    base_hp = ent.Player(mem).max_hp
    assert g.player.max_hp == 42 + lore2.LEGACY["sacrifice"]["bonus"]["max_hp"]
    assert g.player.max_hp > base_hp

    g2, _, _ = new_game(ending="dieu")
    assert g2.player.base_atk >= 5 + lore2.LEGACY["dieu"]["bonus"]["atk"]
    assert g2.souvenirs >= lore2.LEGACY["dieu"]["bonus"]["souvenirs"]


@check("menu : le choix 2 lance le Chapitre II")
def test_menu():
    from game import menu
    mem = temp_memory()
    term = FakeTerm(keys=["2"])
    assert menu.main_menu(term, mem) == "ch2"
    term2 = FakeTerm(keys=["q"])
    assert menu.main_menu(term2, mem) is None


@check("300 tours simulés dans une région sans exception")
def test_simulation():
    g, mem, term = new_game(keys=list("n" * 200), seed=41)
    g.enter_region("audela")
    import random
    rng = random.Random(41)
    for _ in range(300):
        if g.dead:
            break
        g.draw()
        if g.mode != "region":
            g.enter_region("audela")
            continue
        dx, dy = rng.choice(chapter2.DIRS)
        if rng.random() < 0.08:
            g.interact()
        else:
            g.move(dx, dy)


def main() -> int:
    failed = 0
    for name, fn in CHECKS:
        try:
            fn()
            print(f"  OK   {name}")
        except Exception as exc:
            failed += 1
            print(f"  FAIL {name} -> {exc}")
            traceback.print_exc(limit=3)
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} tests Chapitre II passés.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())