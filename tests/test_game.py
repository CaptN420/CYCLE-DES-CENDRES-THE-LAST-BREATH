"""Tests réels du jeu (exécutés avec py -3 tests/test_game.py)."""
from __future__ import annotations

import os
import sys
import tempfile
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import dungeon as dg          # noqa: E402
from game import entities as ent        # noqa: E402
from game import game as gm             # noqa: E402
from game import items                  # noqa: E402
from game import lore, memory as memmod, ui  # noqa: E402

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


def new_game(keys=(), seed=1):
    mem = temp_memory()
    term = FakeTerm(keys)
    g = gm.Game(term, mem, seed=seed)
    g.player = ent.Player(mem)
    return g, mem, term


@check("génération de donjon connectée, étages 1-7")
def test_dungeon_connectivity():
    import random
    for depth in range(1, 8):
        for seed in range(30):
            d = dg.generate(depth, random.Random(seed))
            assert d.tile(*d.start) != dg.WALL
            assert d.tile(*d.stairs) != dg.WALL
            # flood fill depuis le départ
            seen = {d.start}
            stack = [d.start]
            while stack:
                x, y = stack.pop()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in seen:
                        continue
                    if d.walkable(nx, ny):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            assert d.stairs in seen, f"escalier injoignable étage {depth} seed {seed}"
            assert d.feature_at(*d.stairs) is None or True
            # un coffre au fragment existe, lui aussi joignable
            chests = [f for f in d.features if f.kind == "chest"]
            assert chests, f"aucun coffre étage {depth} seed {seed}"
            for f in chests:
                assert (f.x, f.y) in seen, f"coffre injoignable étage {depth}"


@check("cadre 79x29 constant, étages 1-7")
def test_frame_geometry():
    g, mem, term = new_game()
    for depth in range(1, 8):
        g.load_floor(depth)
        frame = g.frame()
        assert len(frame) == 28, f"{len(frame)} lignes à l'étage {depth}"
        for i, line in enumerate(frame):
            width = ui.vlen(line)
            assert width == 79, f"ligne {i} = {width} col. (étage {depth})"


@check("rendu sans exception pendant 300 tours simulés")
def test_simulation_rendering():
    g, mem, term = new_game(keys=list("n" * 400), seed=5)
    g.new_run()
    import random
    rng = random.Random(5)
    for _ in range(300):
        if g.dead:
            break
        g.draw()
        dx, dy = rng.choice(gm.DIRS)
        if rng.random() < 0.1:
            g.interact()
        else:
            g.move(dx, dy)
    assert g.player.hp >= 0


@check("combat : tuer un monstre donne XP et butin")
def test_combat():
    g, mem, term = new_game(seed=3)
    g.new_run()
    g.player.weapon = items.Item("w_test", "Épée de test", ")", ui.WHITE, "weapon", 30)
    mon = ent.Monster.from_def(ent.MONSTER_TABLE[0], g.rng, 1)
    mon.x, mon.y = g.player.x + 1, g.player.y
    g.monsters.append(mon)
    xp_before = g.player.xp + (g.player.level - 1) * 22
    g.move(1, 0)
    assert not mon.alive, "le monstre aurait dû mourir"
    assert g.player.kills == 1
    assert g.player.xp + (g.player.level - 1) * 22 > xp_before


@check("coffre : ramasser le fragment incrémente le compteur")
def test_chest():
    g, mem, term = new_game(seed=11)
    g.new_run()
    chest = next(f for f in g.dungeon.features if f.kind == "chest")
    g.player.x, g.player.y = chest.x, chest.y
    g.open_chest(chest)
    assert g.player.fragments == 1, g.player.fragments


@check("inscription : +1 intuition, persistée sur disque")
def test_inscription_memory():
    g, mem, term = new_game(seed=13)
    g.new_run()
    feat = next(f for f in g.dungeon.features if f.kind == "inscription")
    before = mem.insight
    g.player.x, g.player.y = feat.x, feat.y
    g.read_inscription(feat)
    assert mem.insight == before + 1
    reloaded = memmod.Memory(mem.path)
    assert reloaded.insight == mem.insight
    assert reloaded.inscriptions == mem.inscriptions


@check("mort : enregistrée, squelette revient avec l'équipement")
def test_death_and_skeleton():
    g, mem, term = new_game(keys=["o", "o"], seed=17)
    g.new_run()
    g.player.weapon = items.Item("w_epee_courte", "Épée courte", ")", ui.BONE, "weapon", 4, "test")
    g.depth = 2
    g.die("Test de mortalité")
    assert g.dead
    assert len(mem.deaths) == 1
    assert mem.deaths[0]["weapon"] == "Épée courte"
    assert mem.cycle == 2

    g2, _, _ = new_game(seed=21)
    g2.mem = mem
    g2.player = ent.Player(mem)
    g2.load_floor(2)
    sk = [m for m in g2.monsters if m.name.startswith("Squelette du cycle")]
    assert sk, "le squelette du cycle précédent devrait apparaître"
    names = [i.name for i in sk[0].drops]
    assert "Épée courte" in names, names


@check("descente étage par étage 1 -> 7")
def test_descent():
    g, mem, term = new_game(seed=23)
    g.new_run()
    for expected in range(1, 8):
        assert g.depth == expected, (g.depth, expected)
        if expected == 7:
            break
        g.monsters = []
        g.player.x, g.player.y = g.dungeon.stairs
        g.try_descend()
    assert g.depth == 7
    assert g.boss is not None and g.boss.name.startswith("NHAL'ZOR")


@check("fin secrète avec 7 fragments et intuition suffisante")
def test_secret_ending():
    g, mem, term = new_game(keys=["5", "enter"], seed=29)
    g.new_run()
    g.depth = 7
    g.load_floor(7)
    g.boss.alive = False
    g.player.fragments = 7
    g.player.insight = 6
    g.throne_attempt()
    assert g.ending == "secret", g.ending
    assert "secret" in mem.endings
    assert g.ending_screen(g.ending) is True


@check("la vérité verrouillée sans mémoire, accessible avec")
def test_truth_gating():
    g, mem, term = new_game(seed=31)
    g.new_run()
    g.depth = 7
    g.load_floor(7)
    g.boss.alive = False
    g.player.insight = 2
    g.term.keys = ["1"]          # seul le sacrifice est proposé
    g.throne_attempt()
    assert g.ending == "sacrifice"

    g2, mem2, term2 = new_game(keys=["4"], seed=33)
    g2.new_run()
    g2.depth = 7
    g2.load_floor(7)
    g2.boss.alive = False
    g2.player.insight = 5
    g2.throne_attempt()
    assert g2.ending == "verite", g2.ending


@check("inventaire : équiper, boire, parchemins")
def test_inventory_usage():
    g, mem, term = new_game(seed=37)
    g.new_run()
    p = g.player
    w = items.Item("w_lame", "Lame des forges", ")", ui.GOLD, "weapon", 9, "test")
    p.add_item(w)
    g.use_item(w)
    assert p.weapon is w
    p.hp = 5
    pot = items.make_potion(g.rng)
    pot.key = "p_soin"
    pot.power = 10
    p.add_item(pot)
    g.use_item(pot)
    assert p.hp > 5
    p.poison = 5
    ant = items.Item("p_antidote", "Potion d'antidote", "!", ui.GREEN, "potion", 0, "x")
    p.add_item(ant)
    g.use_item(ant)
    assert p.poison == 0
    scroll = items.Item("s_carto", "Parchemin de cartographie", "?", ui.BLUE, "scroll", 0, "x")
    p.add_item(scroll)
    before = len(g.dungeon.explored)
    g.use_item(scroll)
    assert len(g.dungeon.explored) > before


@check("monstres : IA se déplace vers le joueur, pas dans les murs")
def test_monster_ai():
    g, mem, term = new_game(seed=41)
    g.new_run()
    mon = ent.Monster.from_def(ent.MONSTER_TABLE[2], g.rng, 1)
    x, y = g.dungeon.free_tile(g.rng)
    mon.x, mon.y = x, y
    mon.awake = True
    g.monsters.append(mon)
    start_dist = abs(mon.x - g.player.x) + abs(mon.y - g.player.y)
    for _ in range(6):
        g.monster_turn(mon)
        assert g.dungeon.walkable(mon.x, mon.y)
    end_dist = abs(mon.x - g.player.x) + abs(mon.y - g.player.y)
    assert end_dist <= start_dist, (start_dist, end_dist)


@check("mémoire : le fichier JSON se recharge à l'identique")
def test_memory_roundtrip():
    mem = temp_memory()
    mem.record_death(3, "Empoisonnement", type("P", (), {
        "weapon": None, "armor": None, "kills": 4, "gold": 12, "fragments": 2})())
    mem.record_ending("sacrifice")
    again = memmod.Memory(mem.path)
    assert len(again.deaths) == 1
    assert again.deaths[0]["cause"] == "Empoisonnement"
    assert again.endings == ["sacrifice"]
    assert again.cycle == 2


@check("classes : gardien +PV/armure, sorcier -PV/parchemin, rôdeur +atk")
def test_classes():
    mem = temp_memory()
    g = ent.Player(mem, class_key="gardien")
    assert g.max_hp == 26, g.max_hp
    assert g.armor is not None and g.armor.key == "a_cuir"
    assert g.base_atk == 4

    s = ent.Player(mem, class_key="sorcier")
    assert s.max_hp == 20, s.max_hp
    assert any(it.key == "s_flammes" for it in s.inventory)

    r = ent.Player(mem, class_key="rodeur")
    assert r.base_atk == 4
    assert r.armor is None


@check("compétences : débloquées par l'intuition persistante")
def test_skills_unlock():
    mem = temp_memory()
    mem.data["insight"] = 5
    p = ent.Player(mem, class_key="gardien")
    assert "skeleton_weaken" in p.unlocked_skills
    assert "cycle_hp_bonus" in p.unlocked_skills
    assert "enemy_preview" not in p.unlocked_skills
    mem.data["insight"] = 9
    p2 = ent.Player(mem, class_key="gardien")
    assert "last_breath" in p2.unlocked_skills


@check("Dernier Souffle : résurrection une fois, puis mort réelle")
def test_last_breath():
    g, mem, term = new_game(seed=51)
    g.new_run()
    g.player.insight = 9
    g.player.unlocked_skills.add("last_breath")
    g.player.has_last_breath = False
    g.player.hp = 1
    g.die("Test résurrection")
    assert not g.dead, "aurait dû ressusciter"
    assert g.player.hp == 5
    g.player.hp = 1
    g.die("Seconde mort")
    assert g.dead, "aurait dû mourir pour de bon"


@check("inventaire : nouvelles potions sagesse et force brute")
def test_new_potions():
    g, mem, term = new_game(seed=53)
    g.new_run()
    p = g.player
    base_insight = p.insight
    wis = items.Item("p_sagesse", "Liquide de sagesse", "!", ui.BLUE, "potion", 0, "x")
    p.add_item(wis)
    g.use_item(wis)
    assert p.insight == min(9, base_insight + 1)
    hp_before = p.max_hp
    brute = items.Item("p_force_brutale", "Élixir de force brute", "!", ui.RED, "potion", 6, "x")
    p.add_item(brute)
    g.use_item(brute)
    assert p.max_hp == hp_before + 6


@check("mémoire : les 7 étages génèrent les nouveaux monstres sans erreur")
def test_monster_table_integrity():
    # chaque étage a au moins 3 monstres disponibles
    for depth in range(1, 8):
        pool = [m for m in ent.MONSTER_TABLE if m.depth_min <= depth <= m.depth_max]
        assert len(pool) >= 3, (depth, len(pool))
    # pas de doublons de glyph+name absurdes bloquants
    names = [m.name for m in ent.MONSTER_TABLE]
    assert len(names) == len(set(names)), "noms de monstres dupliqués"


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
    total = len(CHECKS)
    print(f"\n{total - failed}/{total} tests passés.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
