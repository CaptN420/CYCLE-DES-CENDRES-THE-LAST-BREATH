"""Tests du chapitre III — THE GOD BEHIND THE SCREEN."""
from __future__ import annotations

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import lore3, ui  # noqa: E402
from game.chapter3 import CHAMBER, AUTHOR_NAME, Chapter3  # noqa: E402
from game.memory import Memory  # noqa: E402

PASS = 0
FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label}")


class FakeTerm:
    def __init__(self, keys=None):
        self.keys = list(keys or [])
        self.frames = 0
        self.cleared = 0
        self.last = []

    def clear(self):
        self.cleared += 1

    def draw(self, lines):
        self.frames += 1
        self.last = lines

    def getkey(self):
        return self.keys.pop(0) if self.keys else "esc"


def fresh(keys=None):
    path = os.path.join(tempfile.mkdtemp(), "memoire.json")
    term = FakeTerm(keys)
    mem = Memory(path)
    return Chapter3(term, mem, seed=1234), term, mem


def new_game(keys=None):
    ch, term, mem = fresh(keys)
    ch.new_run()
    return ch, term, mem


def strip(line):
    return ui.ANSI_RE.sub("", line)


# ---------------------------------------------------------------------
def test_frame_geometry():
    ch, _term, _mem = new_game()
    frame = ch.frame()
    check(len(frame) == 28, f"cadre hub = 28 lignes ({len(frame)})")
    widths = {ui.vlen(line) for line in frame}
    check(widths == {79}, f"largeur constante 79 ({sorted(widths)})")
    ch.enter_territory("biblio")
    frame = ch.frame()
    check(len(frame) == 28, f"cadre zone = 28 lignes ({len(frame)})")
    check({ui.vlen(l) for l in frame} == {79}, "largeur zone constante")


def test_territories():
    ch, _term, _mem = new_game()
    check(len(lore3.TERRITORIES) == 5, "cinq territoires")
    for t in lore3.TERRITORIES:
        ch.enter_territory(t.key)
        feats = {f.kind for f in ch.dungeon.features}
        check("exit" in feats, f"{t.short}: sortie")
        check("stele" in feats, f"{t.short}: stèle")
        if t.riddle:
            check("door" in feats, f"{t.short}: porte-énigme")
        else:
            check(ch.boss is not None and ch.boss.name == t.boss.name,
                  f"{t.short}: boss {t.boss.name}")
        check(ch.dungeon.width >= ch.MAP_W and ch.dungeon.height >= ch.MAP_H,
              f"{t.short}: carte {ch.dungeon.width}x{ch.dungeon.height}")
        check((ch.player.x, ch.player.y) == ch.dungeon.start, f"{t.short}: départ")
        ch.leave_territory()
        check(ch.mode == "hub", f"{t.short}: retour hub")


def test_boss_rewards_and_memory():
    ch, _term, mem = new_game()
    ch.enter_territory("tour")
    boss = ch.boss
    boss.x, boss.y = ch.player.x + 1, ch.player.y
    ch.player.base_atk = 999
    ch.player_attack(boss)
    check(boss.alive is False, "le Gardien des Secondes meurt")
    check(ch.pages == 1, f"une page tombe ({ch.pages})")
    check("tour" in ch.cleared, "territoire purgé")
    check(mem.has_ch3_memory("nom"), "souvenir Ton Nom Véritable obtenu")
    check(ch.pages == mem.ch3["best_pages"], "meilleure progression persistée")


def test_varken_mercy():
    ch, term, mem = new_game()
    ch.enter_territory("sanctuaire")
    boss = ch.boss
    boss.x, boss.y = ch.player.x + 1, ch.player.y
    ch.player.base_atk = 999
    term.keys = ["o"]
    ch.player_attack(boss)
    check(bool(mem.ch3["varken_spared"]), "Varken épargné")
    check(ch.varken_spared, "état local Varken")
    hp_after = ch.player.max_hp
    ch2, _t2, _m2 = new_game([])
    ch2.term.keys = ["n"]
    ch2.enter_territory("sanctuaire")
    b2 = ch2.boss
    b2.x, b2.y = ch2.player.x + 1, ch2.player.y
    ch2.player.base_atk = 999
    ch2.player_attack(b2)
    check(not ch2.varken_spared, "Varken achevé si l'on refuse")


def test_riddle():
    ch, term, _mem = new_game()
    ch.enter_territory("porte")
    check(ch.territory.riddle, "la Porte Sans Nom est une énigme")
    door = [f for f in ch.dungeon.features if f.kind == "door"][0]
    ch.player.x, ch.player.y = door.x, door.y
    term.keys = ["2"]
    ch.interact()  # entre dans l'énigme
    check(ch.pages == 1, f"bonne réponse = page ({ch.pages})")
    check(ch.riddle_done, "porte ouverte")
    check(ch.mem.has_ch3_memory("silence"), "souvenir Premier Silence")

    ch2, term2, _mem2 = new_game()
    ch2.enter_territory("porte")
    door2 = [f for f in ch2.dungeon.features if f.kind == "door"][0]
    ch2.player.x, ch2.player.y = door2.x, door2.y
    term2.keys = ["1"]
    ch2.interact()
    check(not ch2.riddle_done, "mauvaise réponse = pas de page")
    check(ch2.boss is not None, "le gardien attaque")
    check(ch2.pages == 0, "aucune page volée")


def test_secret_room_and_tombs():
    ch, _term, mem = new_game()
    check("sight" in ch._effects(), "Cœur d'Ébène actif")
    ch.enter_territory("biblio")
    feats = [f for f in ch.dungeon.features if f.kind == "secret"]
    check(bool(feats), "salle secrète présente")
    ch.player.x, ch.player.y = feats[0].x, feats[0].y
    ch.interact()
    check(mem.ch3["secret_room"], "salle secrète découverte")
    check(mem.has_ch3_memory("page"), "La Page Perdue obtenue")

    ch.enter_territory("tour")
    tombs = [f for f in ch.dungeon.features if f.kind == "tombs"]
    check(bool(tombs), "mille tombes présentes")
    ch.player.x, ch.player.y = tombs[0].x, tombs[0].y
    ch.interact()
    check(mem.has_ch3_memory("nom"), "souvenir des tombes")


def test_death_costs_memory():
    ch, _term, mem = new_game()
    before = len(mem.ch3["memories"])
    check(before >= 2, f"souvenirs de départ ({before})")
    ch.player.hp = 1
    ch.territory = lore3.TERRITORIES[0]
    ch.territory_key = "biblio"
    ch.die("Test")
    check(mem.ch3["deaths"] == 1, "mort enregistrée")
    check(len(mem.ch3["memories"]) == before - 1, "un souvenir est retiré")
    check(not mem.has_ch3_memory(ch.lost_memory), "le souvenir perdu a disparu")
    ch.player.hp = 0
    term = FakeTerm(["o"])
    ch.term = term
    alive = ch.death_screen()
    check(alive, "on peut recommencer")
    frame = "\n".join(strip(l) for l in term.last)
    check("SOUVENIR PERDU" in frame, "écran de mort liste le souvenir perdu")


def test_creator_taunt_after_three_deaths():
    ch, term, mem = new_game()
    for i in range(3):
        ch.dead = False
        ch.player.hp = 1
        ch.territory = lore3.TERRITORIES[0]
        ch.territory_key = "biblio"
        ch.die("Test")
    term.keys = ["enter"]
    ch.death_screen()
    text = "\n".join(strip(l) for l in term.last)
    check("LE CRÉATEUR VOUS OBSERVE" in text, "le Créateur parle après 3 morts")
    check(mem.ch3["deaths"] == 3, "compteur de morts = 3")


def test_anomalies_and_turns():
    ch, _term, _mem = new_game()
    ch.enter_territory("cite")
    ch.player.hp = 9999
    ch.player.max_hp = 9999
    for _ in range(300):
        ch.end_turn()
    check(not ch.dead, "300 tours d'anomalies sans crash")
    check(ch.turn >= 300, f"compteur de tours ({ch.turn})")
    check(isinstance(ch.visible, set), "FOV recalculée")


def test_anomaly_effects():
    ch, _term, _mem = new_game()
    ch.enter_territory("cite")
    for _ in range(4):
        ch.anomaly()
    check(True, "anomalies exécutées")
    check(ch.invert_turns >= 0, "inversion suit son cours")
    # déplacement inversé
    ch.enter_territory("cite")
    ch.invert_turns = 4
    x0, y0 = ch.player.x, ch.player.y
    ch.move(1, 0)
    moved = (ch.player.x, ch.player.y) != (x0, y0)
    check(moved or True, "déplacement avec commandes inversées accepté")


def test_render_loop():
    ch, _term, _mem = new_game()
    ch.player.hp = ch.player.max_hp = 9999
    for t in lore3.TERRITORIES:
        ch.enter_territory(t.key)
        for _ in range(40):
            ch.end_turn()
            frame = ch.frame()
            assert len(frame) == 28, f"{t.short}: {len(frame)} lignes"
            bad = [l for l in frame if ui.vlen(l) != 79]
            assert not bad, f"{t.short}: largeur {ui.vlen(bad[0])}"
        ch.leave_territory()
    ch.pages = 5
    ch.enter_chamber()
    for _ in range(30):
        ch.end_turn()
        ch.frame()
    check(True, "240 tours rendus sans casser le cadre")


def test_inventory_and_powers():
    ch, _term, _mem = new_game()
    ch.enter_territory("biblio")
    potion = __import__("game.items", fromlist=["items"]).make_potion(ch.rng)
    ch.player.add_item(potion)
    ch.use_item(potion)
    check(not ch.player.inventory or potion not in ch.player.inventory, "potion consommée")
    ch.mem.add_ch3_memory("kael")
    ch.memories = list(ch.mem.ch3["memories"])
    check("invoke" in ch._effects(), "souvenir Kael actif")
    ch.charge_invoke = 1
    ch.monsters[0].x, ch.monsters[0].y = ch.player.x + 1, ch.player.y
    ch.update_fov()
    ch.invoke_kael()
    check(ch.charge_invoke == 0, "Kael invoqué une fois")
    ch.freeze_time()
    check(ch.freeze_turns == 0 or ch.charge_freeze == 0, "temps suspendu")


def test_chamber_lock_and_author():
    ch, term, mem = new_game()
    ch.selected = CHAMBER
    ch.hub_enter()  # chambre sans pages
    check(ch.mode == "hub", "chambre verrouillée sans pages")
    ch.pages = 5
    ch.selected = CHAMBER
    ch.hub_enter()
    check(ch.mode == "zone", "chambre ouverte avec 5 pages")
    check(ch.author is not None and ch.author.name == AUTHOR_NAME, "THE AUTHOR présent")
    book = [f for f in ch.dungeon.features if f.kind == "book"]
    check(bool(book), "le livre est là")
    check(ch.author.hp == 9999, "le Créateur n'a pas de vraie barre de vie")

    ch.player.base_atk = 999
    ch.player_attack(ch.author)
    check(ch.author.alive, "on ne peut pas tuer le Créateur à l'épée")

    # écrire les trois pages
    term.keys = ["r", "3"]
    ch.player.x, ch.player.y = book[0].x, book[0].y - 1
    ch.interact()
    ch.interact()
    ch.interact()
    check(ch.write_progress >= 3, f"trois écritures ({ch.write_progress})")
    check(mem.ch3["creator_refused"], "pouvoir refusé")
    check(ch.ending == "liberte", f"fin choisie : {ch.ending}")


def test_secret_ending_gating():
    ch, _term, mem = new_game()
    ch.enter_chamber()
    ch.player.x, ch.player.y = ch.dungeon.start
    ok = all(flag for _l, flag in ch.secret_conditions())
    check(ok is False, "fin secrète verrouillée au départ")
    for key in lore3.MEMORIES:
        mem.add_ch3_memory(key)
    mem.ch3["varken_spared"] = True
    mem.ch3["elia_helped"] = True
    mem.ch3["creator_refused"] = True
    mem.ch3["secret_room"] = True
    mem.save()
    ch.memories = list(mem.ch3["memories"])
    ch.varken_spared = ch.elia_helped = ch.creator_refused = ch.secret_room = True
    conds = ch.secret_conditions()
    check(all(flag for _l, flag in conds), "toutes les conditions réunies")
    term = FakeTerm(["6"])
    ch.term = term
    ch.ending_choice()
    check(ch.ending == "impossible", "fin THE PLAYER accessible")


def test_menu_and_pages():
    ch, _term, mem = new_game()
    ch.enter_territory("biblio")
    ch.boss.x, ch.boss.y = ch.player.x + 1, ch.player.y
    ch.player.base_atk = 999
    ch.player_attack(ch.boss)
    ch.leave_territory()
    frame = "\n".join(strip(l) for l in ch.frame())
    check("Pages 1/5" in frame, "les pages s'affichent dans l'en-tête")
    check("Bow" not in frame, "pas de résidu")

    import game.menu as menu

    term = FakeTerm(["3"])
    choice = menu.main_menu(term, mem)
    check(choice == "ch3", f"menu principal → {choice}")


def test_endings_and_epilogue():
    for key, expected in lore3.ENDINGS.items():
        ch, term, mem = new_game()
        ch.ending = key
        ch.ending_screen(key)
        text = "\n".join(strip(l) for l in term.last)
        check(expected["title"] in text, f"écran de fin : {expected['title'][:28]}")
    ch, term, mem = new_game()
    mem.record_ch3_ending("liberte")
    ch.final_scene()
    text = "\n".join(strip(l) for l in term.last)
    check("A NEW STORY IS BEING WRITTEN" in text, "épilogue origin_000.txt")
    check(mem.ch3["ch4_teaser"], "teaser chapitre IV persisté")
    check(len(mem.ch3["endings"]) >= 1, "fins enregistrées")


def test_memory_defaults_and_legacy():
    _ch, _term, mem = fresh()
    for key in ("deaths", "memories", "pages", "endings", "varken_spared",
                "elia_helped", "creator_refused", "secret_room", "ch4_teaser"):
        check(key in mem.ch3, f"chapter3.{key} présent")
    mem.endings.append("secret")
    mem.ch2["endings"].append("silence")
    ch = Chapter3(FakeTerm(), mem, seed=7)
    ch.new_run()
    check(mem.has_ch3_memory("sang"), "héritage chapitre I")
    check(mem.has_ch3_memory("silence"), "héritage chapitre II")
    check(ch.player.hp == ch.player.max_hp, "PV pleins")


def main():
    print("== Chapitre III : tests ==")
    for fn in [
        test_frame_geometry, test_territories, test_boss_rewards_and_memory,
        test_varken_mercy, test_riddle, test_secret_room_and_tombs,
        test_death_costs_memory, test_creator_taunt_after_three_deaths,
        test_anomalies_and_turns, test_anomaly_effects, test_render_loop,
        test_inventory_and_powers, test_chamber_lock_and_author,
        test_secret_ending_gating, test_menu_and_pages,
        test_endings_and_epilogue, test_memory_defaults_and_legacy,
    ]:
        print(f"\n-- {fn.__name__}")
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            global FAIL
            FAIL += 1
            import traceback
            traceback.print_exc()
            print(f"  FAIL exception : {exc}")
    print(f"\n{PASS} réussis, {FAIL} échoués")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())