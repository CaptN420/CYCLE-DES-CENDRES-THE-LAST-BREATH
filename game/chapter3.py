"""CHAPITRE III — THE GOD BEHIND THE SCREEN : l'Intervalle, l'Author, six fins."""
from __future__ import annotations

import math
import random

from . import dungeon as dg
from . import entities as ent
from . import familiar as fam_mod
from . import familiar_field
from . import item_db, item_manager, items, lore3, loot_manager, ui

KEYMAP = {
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
    "k": (0, -1), "j": (0, 1), "h": (-1, 0), "l": (1, 0),
    "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1),
    "UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0),
}

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]

CHAMBER = "chambre"
AUTHOR_NAME = "THE AUTHOR"


class Chapter3(familiar_field.FamiliarField):
    MAP_W = 46
    MAP_H = 16
    PANEL_W = 30
    INNER = MAP_W + 1 + PANEL_W

    def __init__(self, term, memory, seed: int | None = None):
        self.term = term
        self.mem = memory
        self.seed = seed
        self.rng = random.Random(seed)
        self.messages: list[tuple[str, int]] = []
        self.player: ent.Player | None = None
        self.mode = "hub"
        self.territory: lore3.Territory | None = None
        self.territory_key: str | None = None
        self.dungeon: dg.Dungeon | None = None
        self.monsters: list[ent.Monster] = []
        self.ground: list[dict] = []
        self.visible: set[tuple[int, int]] = set()
        self.selected = "biblio"
        self.turn = 0
        self.dead = False
        self.dead_cause = ""
        self.ending: str | None = None
        self.quit_run = False
        self.pages = 0
        self.memories: list[str] = []
        self.cleared: set[str] = set()
        self.invert_turns = 0
        self.freeze_turns = 0
        self.charge_invoke = 1
        self.charge_freeze = 1
        self.boss: ent.Monster | None = None
        self.author: ent.Monster | None = None
        self.write_progress = 0
        self.cancel_next_attack = False
        self.elia_helped = False
        self.varken_spared = False
        self.creator_refused = False
        self.secret_room = False
        self.riddle_done = False
        self.last_hit_by = ""
        self.familiar = None
        self.fam_taunt = 0
        self.player_guard = 0

    # =================================================================
    #  ÉCRANS
    # =================================================================
    def modal(self, title: str, body: list[str], footer: str,
              colour: int = ui.GOLD, width: int = 72) -> str:
        inner = width - 2
        lines = ["╔" + "═" * inner + "╗"]
        lines.append("║" + ui.pad(ui.paint(title, colour, bold=True), inner, "center") + "║")
        lines.append("╠" + "═" * inner + "╣")
        for row in body:
            if not row:
                lines.append("║ " + " " * (inner - 2) + " ║")
                continue
            if "\x1b" in row or len(row) <= inner - 2:
                chunks = [row]
            else:
                chunks = ui.wrap(row, inner - 2)
            for chunk in chunks:
                lines.append("║ " + ui.pad(chunk, inner - 2) + " ║")
        lines.append("╠" + "═" * inner + "╣")
        lines.append("║ " + ui.pad(ui.paint(footer, ui.GREY), inner - 2) + " ║")
        lines.append("╚" + "═" * inner + "╝")
        self.term.clear()
        self.term.draw([""] + lines)
        return self.term.getkey()

    def ask(self, prompt: str) -> bool:
        while True:
            if self.player is not None:
                self.draw(ui.paint(" " + prompt, ui.GOLD, bold=True))
            else:
                self.term.clear()
                self.term.draw(["", "  " + ui.paint(prompt, ui.GOLD, bold=True)])
            key = self.term.getkey().lower()
            if key in ("o", "y", "enter", "space", " "):
                return True
            if key in ("n", "q", "esc"):
                return False

    def continuity_screen(self) -> bool:
        ch1 = self.mem.endings[-1] if self.mem.endings else "aucun"
        ch2 = self.mem.ch2["endings"][-1] if self.mem.ch2["endings"] else "aucun"
        body = ["", ui.paint("CHAPITRE I", ui.GOLD, bold=True),
                "  " + lore3.CH1_LEGACY.get(ch1, lore3.CH1_LEGACY["aucun"]),
                "",
                ui.paint("CHAPITRE II", ui.GOLD, bold=True),
                "  " + lore3.CH2_LEGACY.get(ch2, lore3.CH2_LEGACY["aucun"]),
                "",
                ui.paint("─" * 58, ui.DARKGREY),
                ui.paint("Souvenirs importés :", ui.CYAN)]
        imported = self.import_memories()
        if imported:
            for key in imported:
                body.append(f"  · {lore3.MEMORIES[key]['name']}")
        else:
            body.append("  (aucun — le récit te précède à peine)")
        body.append("")
        body.append(ui.paint(f"Âmes perdues au chapitre III : {self.mem.ch3['deaths']}", ui.PURPLE))
        body.append(ui.paint(f"Fin(s) du chapitre III : {len(self.mem.ch3['endings'])}/6", ui.MIDGREY))
        k = self.modal("LES TROIS HISTOIRES QUE TU AS TRAVERSÉES", body,
                       "[Entrée] entrer dans l'Intervalle   ·   [Q] renoncer", ui.MAGENTA).lower()
        return not (k == "q" or k == "esc")

    def import_memories(self) -> list[str]:
        ch3 = self.mem.ch3
        granted = []
        imports = {
            "ebene": True,
            "eldria": True,
            "sang": bool(self.mem.endings) or bool(self.mem.deaths),
            "kael": bool(self.mem.ch2["kael_ally"]) or int(self.mem.ch2["deaths"]) >= 3,
            "silence": bool(self.mem.ch2["endings"]),
        }
        for key, condition in imports.items():
            if condition and key not in ch3["memories"]:
                ch3["memories"].append(key)
                granted.append(key)
        if granted:
            self.mem.save()
        return granted

    def prologue(self) -> None:
        self.modal(lore3.TITLE, [""] + [ui.paint(l, ui.BONE) if l else "" for l in lore3.PROLOGUE]
                   + ["", ui.paint(lore3.SUBTITLE, ui.PURPLE)],
                   "[Entrée] t'éveiller dans l'Intervalle", ui.MAGENTA, 74)
        self.modal("L'INTERVALLE", [""] + [ui.paint(l, ui.BONE) if l else "" for l in lore3.INTERVALLE],
                   "[Entrée] écouter la voix", ui.PURPLE, 74)

    # =================================================================
    #  PARTIE
    # =================================================================
    def new_run(self) -> None:
        if not self.mem.ch3["memories"]:
            self.import_memories()
        class_key = self.mem.data.get("class", "gardien")
        if class_key not in ent.CLASS_DEFS:
            class_key = "gardien"
        p = ent.Player(self.mem, class_key=class_key)
        self.player = p
        p.level = 7
        p.max_hp = 84
        p.base_atk = 9
        p.hp = p.max_hp
        p.weapon = items.make_ch2_weapon(2)
        p.armor = items.make_ch2_armor(2)
        p.xp = 0
        p.x = p.y = 0
        for _ in range(3):
            p.add_item(items.Item("p_soin", "Potion de soin", "!", ui.BRIGHTRED,
                                  "potion", 14, "Une chaleur rouge dans la gorge."))

        ch3 = self.mem.ch3
        self.memories = list(ch3["memories"])
        self.elia_helped = bool(ch3.get("elia_helped", False))
        self.varken_spared = bool(ch3.get("varken_spared", False))
        self.creator_refused = bool(ch3.get("creator_refused", False))
        self.secret_room = bool(ch3.get("secret_room", False))
        if "defense" in self._effects():
            p.base_def += 1
        if "resistance" in self._effects():
            p.base_def += 1

        self.load_familiar()
        p.x = p.y = 0

        self.pages = 0
        self.cleared = set()
        self.mode = "hub"
        self.territory = None
        self.territory_key = None
        self.dungeon = None
        self.monsters = []
        self.ground = []
        self.turn = 0
        self.dead = False
        self.dead_cause = ""
        self.ending = None
        self.quit_run = False
        self.invert_turns = 0
        self.freeze_turns = 0
        self.selected = "biblio"
        self.write_progress = 0
        self.messages = []
        self.log(lore3.TITLE, ui.GOLD)
        self.log(f"Souvenirs portés : {len(self.memories)}/7. Pages du livre : 0/5.", ui.PURPLE)
        if int(ch3["deaths"]):
            self.log(f"Le Créateur t'a déjà vu mourir {ch3['deaths']} fois.", ui.RED)

    def _effects(self) -> set[str]:
        return {lore3.MEMORIES[k]["effect"] for k in self.memories if k in lore3.MEMORIES}

    def play(self) -> tuple[str, str]:
        while True:
            self.draw()
            key = self.term.getkey()
            self.handle(key)
            if self.dead:
                return ("dead", self.dead_cause)
            if self.ending:
                return ("ending", self.ending)
            if self.quit_run:
                return ("quit", "")

    def handle(self, key: str) -> None:
        low = key.lower()
        if self.mode == "hub":
            self.handle_hub(key, low)
        else:
            self.handle_zone(key, low)

    # =================================================================
    #  HUB — L'INTERVALLE
    # =================================================================
    def handle_hub(self, key: str, low: str) -> None:
        if low in KEYMAP:
            self.hub_move(*KEYMAP[low])
            return
        if low in ("1", "2", "3", "4", "5"):
            idx = int(low) - 1
            if idx < len(lore3.TERRITORIES):
                self.selected = lore3.TERRITORIES[idx].key
            return
        if low in ("6", "0"):
            self.selected = CHAMBER
            return
        if low in ("e", "enter", "space", " "):
            self.hub_enter()
            return
        if low == "i":
            self.open_inventory()
            return
        if low == "p":
            self.companion_menu()
            return
        if low == "o":
            self.journal()
            return
        if low == "?":
            self.show_help()
            return
        if low == "r":
            gain = self.player.heal(max(1, self.player.max_hp // 4))
            self.log(f"Tu t'accordes un instant hors du temps. +{gain} PV.", ui.GREEN)
            return
        if low == "q":
            if self.ask("Quitter le Chapitre III ? (la progression persiste) (o/n)"):
                self.quit_run = True
            return

    def hub_move(self, dx: int, dy: int) -> None:
        if self.selected == CHAMBER:
            cx, cy = lore3.CHAMBER_POS
        else:
            cx, cy = lore3.TERRITORY_BY_KEY[self.selected].pos
        best, best_score = None, 0.25
        targets = [(t.key, t.pos) for t in lore3.TERRITORIES] + [(CHAMBER, lore3.CHAMBER_POS)]
        for key, (x, y) in targets:
            if key == self.selected:
                continue
            vx, vy = x - cx, y - cy
            norm = math.hypot(vx, vy) or 1.0
            score = (vx * dx + vy * dy) / norm
            if score > best_score:
                best, best_score = key, score
        if best:
            self.selected = best

    def hub_enter(self) -> None:
        if self.selected == CHAMBER:
            if self.pages >= 5:
                self.enter_chamber()
            else:
                self.log(f"Le livre n'a que {self.pages}/5 pages. La porte reste fermée.", ui.MAGENTA)
                self.log("« Ce n'est pas encore une histoire complète », murmure l'air.", ui.PURPLE)
            return
        self.enter_territory(self.selected)

    # =================================================================
    #  TERRITOIRES
    # =================================================================
    def enter_territory(self, key: str) -> None:
        territory = lore3.TERRITORY_BY_KEY[key]
        self.territory = territory
        self.territory_key = key
        self.mode = "zone"
        depth = lore3.TERRITORIES.index(territory) + 1
        self.dungeon = dg.generate(depth, self.rng)
        self.monsters = []
        self.ground = []
        self.turn = 0
        self.invert_turns = 0
        self.freeze_turns = 0
        self.charge_invoke = 1 if "invoke" in self._effects() else 0
        self.charge_freeze = 1 if "freeze" in self._effects() else 0
        px, py = self.dungeon.start
        self.player.x, self.player.y = px, py
        self.dungeon.set_tile(px, py, "<")
        self.dungeon.features.append(dg.Feature(px, py, "exit", {}))
        self.place_familiar(px, py)
        self.boss = None
        avoid = {(px, py), self.dungeon.stairs}

        if key not in self.cleared:
            bx, by = self.dungeon.stairs
            if territory.riddle:
                self.dungeon.set_tile(bx, by, dg.THRONE)
                self.dungeon.features.append(dg.Feature(bx, by, "door", {}))
                self.log("Une porte immense. Aucun monstre ne la garde — seulement un mot.", ui.WHITE)
            else:
                boss = ent.Monster.from_def(territory.boss, self.rng, depth)
                boss.x, boss.y = bx, by
                boss.awake = True
                self.monsters.append(boss)
                self.boss = boss
            for _ in range(5 + depth):
                mx = my = -1
                for _ in range(80):
                    mx, my = self.dungeon.free_tile(self.rng, avoid)
                    if abs(mx - px) + abs(my - py) >= 6:
                        break
                avoid.add((mx, my))
                mon = ent.Monster.from_def(self.rng.choice(territory.monsters), self.rng, depth)
                mon.x, mon.y = mx, my
                self.monsters.append(mon)

        # PNJ
        if territory.npc:
            npc = lore3.NPCS[territory.npc]
            room = self.rng.choice(self.dungeon.rooms[1:])
            nx, ny = self.dungeon.free_tile(self.rng, avoid, [room])
            avoid.add((nx, ny))
            self.dungeon.set_tile(nx, ny, npc["glyph"])
            self.dungeon.features.append(dg.Feature(nx, ny, "npc", {"key": territory.npc}))

        # stèle / inscriptions de l'Intervalle
        sx, sy = self.dungeon.free_tile(self.rng, avoid)
        avoid.add((sx, sy))
        self.dungeon.set_tile(sx, sy, dg.INSCRIPTION)
        self.dungeon.features.append(dg.Feature(sx, sy, "stele", {"text": territory.stele}))

        # source de l'Intervalle : une seule gorgée par territoire
        fx, fy = self.dungeon.free_tile(self.rng, avoid)
        avoid.add((fx, fy))
        self.dungeon.set_tile(fx, fy, dg.SHRINE)
        self.dungeon.features.append(dg.Feature(fx, fy, "shrine", {}))

        # la salle des mille tombes (Tour du Temps Mort)
        if key == "tour":
            tx, ty = self.dungeon.free_tile(self.rng, avoid)
            avoid.add((tx, ty))
            self.dungeon.set_tile(tx, ty, dg.SHRINE)
            self.dungeon.features.append(dg.Feature(tx, ty, "tombs", {}))

        # salle secrète de la Bibliothèque (Cœur d'Ébène)
        if key == "biblio" and "sight" in self._effects() and not self.secret_room:
            rx, ry = self.dungeon.free_tile(self.rng, avoid)
            avoid.add((rx, ry))
            self.dungeon.set_tile(rx, ry, dg.SHRINE)
            self.dungeon.features.append(dg.Feature(rx, ry, "secret", {}))

        self.update_fov()
        self.log(f"— {territory.name} —", ui.GOLD)
        self.log(territory.subtitle, ui.MIDGREY)
        self.log(self.rng.choice(territory.ambient), ui.GREY)
        self.log("[<] revenir à l'Intervalle.", ui.MIDGREY)

    def enter_chamber(self) -> None:
        self.territory = None
        self.territory_key = CHAMBER
        self.mode = "zone"
        self.dungeon = dg.generate(7, self.rng)
        self.monsters = []
        self.ground = []
        self.turn = 0
        self.write_progress = 0
        px, py = self.dungeon.start
        self.player.x, self.player.y = px, py
        self.dungeon.set_tile(px, py, "<")
        self.dungeon.features.append(dg.Feature(px, py, "exit", {}))
        self.place_familiar(px, py)
        # la chambre : une table, un livre, une chaise — dans la même salle que toi
        bx, by = self.dungeon.stairs
        room = self.dungeon.rooms[0]
        candidates = [(x, y) for y in range(room.y, room.y + room.h)
                      for x in range(room.x, room.x + room.w)
                      if 2 <= abs(x - px) + abs(y - py) <= 4
                      and self.dungeon.tile(x, y) == dg.FLOOR]
        if candidates:
            bx, by = candidates[len(candidates) // 2]
        self.dungeon.set_tile(bx, by, "B")
        self.dungeon.features.append(dg.Feature(bx, by, "book", {}))
        self.author = ent.Monster(AUTHOR_NAME, "A", ui.WHITE, 9999, 9999, 16, 0,
                                  frozenset(), True)
        ax = bx + 2
        if self.dungeon.tile(ax, by) != dg.FLOOR:
            ax = bx - 2
        self.author.x = ax if self.dungeon.walkable(ax, by) else bx
        self.author.y = by
        self.author.awake = True
        self.monsters.append(self.author)
        self.update_fov()
        self.log("— LA CHAMBRE DE L'AUTEUR —", ui.WHITE)
        self.log("Une table. Un livre. Une chaise.", ui.BONE)
        self.log("THE LAST BREATH — COMPLETE EDITION", ui.GOLD)
        for line in lore3.AUTHOR_LINES[:2]:
            self.log(line, ui.WHITE)

    def leave_territory(self) -> None:
        if self.territory_key == CHAMBER:
            self.log("La chambre n'a pas de sortie. Seulement une page.", ui.MAGENTA)
            return
        self.mode = "hub"
        self.territory = None
        self.territory_key = None
        self.monsters = []
        self.ground = []
        self.dungeon = None
        self.invert_turns = 0
        gain = self.player.heal(self.player.max_hp // 8)
        self.log(f"Tu reviens entre deux réalités. +{gain} PV.", ui.MIDGREY)

    # =================================================================
    #  DÉPLACEMENT / COMBAT
    # =================================================================
    def has_los(self, ax: int, ay: int, bx: int, by: int) -> bool:
        for x, y in list(dg._line(ax, ay, bx, by))[1:-1]:
            if self.dungeon.tile(x, y) == dg.WALL:
                return False
        return True

    def monster_at(self, x: int, y: int) -> ent.Monster | None:
        for m in self.monsters:
            if m.alive and not m.spared and (m.x, m.y) == (x, y):
                return m
        return None

    def update_fov(self) -> None:
        radius = 10 if "sight" in self._effects() else 8
        self.visible = dg.compute_fov(self.dungeon, self.player.x, self.player.y, radius)

    def handle_zone(self, key: str, low: str) -> None:
        if low in KEYMAP:
            dx, dy = KEYMAP[low]
            if self.invert_turns > 0:
                dx, dy = -dx, -dy
            self.move(dx, dy)
            return
        if low in ("e", "enter"):
            self.interact()
            return
        if low == "<":
            self.leave_territory()
            return
        if low == "i":
            self.open_inventory()
            return
        if low == "o":
            self.journal()
            return
        if low == "p":
            self.companion_menu()
            return
        if low == "h":
            self.quick_heal()
            return
        if low == "v":
            self.invoke_kael()
            return
        if low == "f":
            self.freeze_time()
            return
        if low == "?":
            self.show_help()
            return
        if low == "q":
            if self.ask("Quitter le Chapitre III ? (la progression persiste) (o/n)"):
                self.quit_run = True
            return
        if low == "r":
            self.log("Tu attends. Le monde attend aussi, mais autrement.", ui.MIDGREY)
            self.end_turn()

    def move(self, dx: int, dy: int) -> None:
        if self.dead or self.ending or self.mode not in ("zone",) or self.dungeon is None:
            return
        p = self.player
        nx, ny = p.x + dx, p.y + dy
        mon = self.monster_at(nx, ny)
        if mon:
            self.player_attack(mon)
            if not self.dead and not self.ending:
                self.end_turn()
            return
        if not self.dungeon.walkable(nx, ny):
            self.log("L'Intervalle refuse ce pas.", ui.MIDGREY)
            return
        p.x, p.y = nx, ny
        self.auto_pickup()
        self.update_fov()
        self.check_tile()
        if not self.dead:
            self.end_turn()

    def auto_pickup(self) -> None:
        p = self.player
        for g in list(self.ground):
            if (g["x"], g["y"]) != (p.x, p.y):
                continue
            item = g["item"]
            if item.owner == "familiar":
                self.log("Ce butin appartient à ton familier. Tu n'y touches pas.", ui.MIDGREY)
                continue
            self.ground.remove(g)
            self.log(p.add_item(item), ui.BONE)

    def check_tile(self) -> None:
        feat = self.dungeon.feature_at(self.player.x, self.player.y)
        if feat and feat.kind == "exit":
            self.log("Une couture de l'Intervalle. [<] pour sortir.", ui.GOLD)
        elif feat and feat.kind == "book":
            self.log("Le livre est ouvert à la dernière page. [E] pour écrire.", ui.GOLD)

    def player_attack(self, mon: ent.Monster) -> None:
        p = self.player
        if mon.name == AUTHOR_NAME:
            self.log("Tu frappes l'air : il a déjà réécrit ton geste.", ui.WHITE)
            self.author_retaliate()
            return
        if self.cancel_next_attack:
            self.cancel_next_attack = False
            self.log("Ta main traverse le vide. Le Créateur a barré ton attaque.", ui.PURPLE)
            return
        dmg = p.damage_roll(self.rng)
        killed = mon.take_damage(dmg)
        weapon = p.weapon.name if p.weapon else "tes poings"
        self.log(f"Tu frappes {mon.name} avec {weapon} : {dmg} dégâts.", ui.WHITE)
        if killed:
            self.on_monster_death(mon)

    def on_monster_death(self, mon: ent.Monster, killer: str = "player") -> None:
        if killer == "familiar":
            self.on_familiar_kill(mon)
            return
        p = self.player
        p.kills += 1
        self.log(f"{mon.name} s'effondre — et se relit une dernière fois.", ui.RED)
        for note in p.gain_xp(mon.xp):
            self.log(note, ui.GREEN)
        drops = loot_manager.roll_loot(mon, "player", self.depth, self.rng, chance=0.5)
        for it in drops:
            self.ground.append({"x": mon.x, "y": mon.y, "item": it})
        if drops:
            self.log("Le butin est à toi. Ton familier n'y touchera pas.", ui.MIDGREY)
        if mon.boss:
            self.boss_reward(mon, killer="player")

    def boss_reward(self, mon: ent.Monster, killer: str = "player") -> None:
        key = self.territory_key or ""
        if key in self.cleared:
            return
        self.cleared.add(key)
        self.pages += 1
        self.mem.ch3["pages"] = max(int(self.mem.ch3.get("best_pages", 0)), self.pages)
        self.mem.ch3["best_pages"] = self.mem.ch3["pages"]
        self.mem.save()
        self.log(f"Une page du livre tombe de lui. ({self.pages}/5)", ui.YELLOW)
        for it in loot_manager.boss_loot("player", self.depth, self.rng, self.player.class_key):
            self.ground.append({"x": mon.x, "y": mon.y, "item": it})
        if self.familiar is not None:
            for it in loot_manager.boss_loot("familiar", self.depth, self.rng,
                                             self.familiar.class_key):
                self.ground.append({"x": mon.x, "y": mon.y, "item": it})
            self.log("Une part de butin revient à ton familier — la sienne.", ui.CYAN)
        if key == "sanctuaire":
            self.offer_varken_mercy()
        if key == "porte" and self.mem.add_ch3_memory("silence"):
            self.memories = list(self.mem.ch3["memories"])
            self.log("Souvenir : Le Premier Silence.", ui.CYAN)
        if key == "tour" and self.mem.add_ch3_memory("nom"):
            self.memories = list(self.mem.ch3["memories"])
            self.log("Souvenir : Ton Nom Véritable. Les tombes te reconnaissent.", ui.CYAN)
        if self.pages >= 5:
            self.log("Cinq pages. La Chambre de l'Auteur s'ouvre au centre.", ui.MAGENTA)

    def monster_attack(self, mon: ent.Monster) -> None:
        p = self.player
        raw = self.rng.randint(max(1, mon.atk - 3), mon.atk + 1)
        dmg = max(1, raw - p.defense)
        if "resistance" in self._effects():
            dmg = max(1, dmg - 2)
        if self.player_guard > 0:
            self.player_guard -= 1
            dmg = max(1, dmg // 2)
            self.log("Ton familier amortit le coup.", ui.BONE)
        p.hurt(dmg)
        self.last_hit_by = mon.name
        self.log(f"{mon.name} te frappe : {dmg} dégâts.", ui.RED)
        if "poison" in mon.traits and self.rng.random() < 0.3 and p.poison <= 0:
            p.poison = 6
            self.log("Le venin n'a pas été écrit pour toi. Il te ronge quand même.", ui.GREEN)
        if "drain" in mon.traits and self.rng.random() < 0.25 and p.max_hp > 10:
            p.max_hp -= 1
            p.hp = min(p.hp, p.max_hp)
            self.log("Il te retire un souvenir de plus.", ui.PURPLE)
        if p.hp <= 0:
            self.die(self.last_hit_by or mon.name)

    def die(self, cause: str) -> None:
        if self.dead:
            return
        p = self.player
        p.hp = 0
        self.dead = True
        self.dead_cause = cause
        self.mem.record_ch3_death(self.territory_key or "intervalle", cause, p)
        # le Créateur retire un souvenir
        if self.memories:
            lost = self.rng.choice(self.memories)
            self.mem.remove_ch3_memory(lost)
            self.memories.remove(lost)
            self.lost_memory = lost
        else:
            self.lost_memory = ""

    def end_turn(self) -> None:
        if self.dead:
            return
        p = self.player
        self.turn += 1
        if self.invert_turns > 0:
            self.invert_turns -= 1
            if self.invert_turns == 0:
                self.log("Les commandes reviennent à la normale.", ui.MIDGREY)
        if p.poison > 0:
            p.poison -= 1
            if p.poison % 2 == 0:
                p.hurt(1)
                self.log("Le poison te ronge. (-1 PV)", ui.GREEN)
                if p.hp <= 0:
                    self.die("Empoisonnement")
                    return
        if self.turn % 12 == 0 and p.hp < p.max_hp and p.poison == 0:
            p.heal(1)

        if self.freeze_turns > 0:
            self.freeze_turns -= 1
            if self.freeze_turns == 0:
                self.log("Le temps reprend son souffle ennemi.", ui.CYAN)
        else:
            for mon in list(self.monsters):
                if not mon.alive or mon.spared or self.dead:
                    continue
                self.monster_turn(mon)
        if self.dead:
            return

        if not self.dead:
            self.familiar_turn()

        if self.territory_key == CHAMBER:
            self.author_turn()
        elif self.rng.random() < 0.09:
            self.anomaly()

    def _target_of(self, mon: ent.Monster) -> tuple[int, int, bool]:
        """Le familier attire-t-il ce monstre ? Retourne (x, y, est_familier)."""
        p = self.player
        fam = self.familiar
        if fam is None or not fam.alive:
            return p.x, p.y, False
        d_player = abs(mon.x - p.x) + abs(mon.y - p.y)
        d_fam = abs(mon.x - fam.x) + abs(mon.y - fam.y)
        if self.fam_taunt > 0 and d_fam <= d_player + 3:
            return fam.x, fam.y, True
        if d_fam <= 1 and d_player > 2 and self.rng.random() < 0.4:
            return fam.x, fam.y, True
        return p.x, p.y, False

    def monster_attack_familiar(self, mon: ent.Monster) -> None:
        fam = self.familiar
        if fam is None or not fam.alive:
            return
        raw = self.rng.randint(max(1, mon.atk - 3), mon.atk + 1)
        note = fam.take_damage(raw)
        self.log(note, ui.RED if fam.alive else ui.MAGENTA)
        if not fam.alive:
            self.log(f"{fam.name} est hors combat. Il reviendra dans quelques tours.", ui.PURPLE)
            self.save_familiar()

    def monster_turn(self, mon: ent.Monster) -> None:
        p = self.player
        tx, ty, is_fam = self._target_of(mon)
        dist = abs(mon.x - tx) + abs(mon.y - ty)
        if not mon.awake:
            if dist <= 9 and self.has_los(mon.x, mon.y, p.x, p.y):
                mon.awake = True
            elif self.rng.random() < 0.3:
                self._step_random(mon)
                return
            else:
                return
        steps = 2 if "fast" in mon.traits else 1
        for _ in range(steps):
            if self.dead:
                return
            if abs(mon.x - tx) <= 1 and abs(mon.y - ty) <= 1:
                if (tx, ty) == (p.x, p.y):
                    self.monster_attack(mon)
                else:
                    self.monster_attack_familiar(mon)
                continue
            dx = (tx > mon.x) - (tx < mon.x)
            dy = (ty > mon.y) - (ty < mon.y)
            options = ([(dx, 0), (0, dy)] if abs(p.x - mon.x) >= abs(p.y - mon.y)
                       else [(0, dy), (dx, 0)])
            options += [d for d in DIRS if d not in options]
            moved = False
            for ddx, ddy in options:
                nx, ny = mon.x + ddx, mon.y + ddy
                if not self.dungeon.walkable(nx, ny):
                    continue
                if self.monster_at(nx, ny) or (nx, ny) == (tx, ty):
                    continue
                mon.x, mon.y = nx, ny
                moved = True
                break
            if not moved:
                break

    def _step_random(self, mon: ent.Monster) -> None:
        ddx, ddy = self.rng.choice(DIRS)
        nx, ny = mon.x + ddx, mon.y + ddy
        if self.dungeon.walkable(nx, ny) and not self.monster_at(nx, ny):
            if (nx, ny) != (self.player.x, self.player.y):
                mon.x, mon.y = nx, ny

    # =================================================================
    #  ANOMALIES DE RÉALITÉ
    # =================================================================
    def anomaly(self) -> None:
        text = self.rng.choice(lore3.ANOMALIES)
        self.log(text, ui.MAGENTA)
        roll = self.rng.random()
        p = self.player
        if roll < 0.22:
            self.invert_turns = 4
            self.log("Tes pieds obéissent à quelqu'un d'autre. (4 tours)", ui.RED)
        elif roll < 0.40:
            mon = self._random_monster()
            if mon:
                for _ in range(40):
                    mx, my = self.dungeon.free_tile(self.rng)
                    if abs(mx - p.x) + abs(my - p.y) <= 3 and (mx, my) != (p.x, p.y):
                        mon.x, mon.y = mx, my
                        mon.awake = True
                        self.monsters.append(mon)
                        self.log("Quelque chose apparaît trop près de toi.", ui.RED)
                        break
        elif roll < 0.55:
            mon = self.monster_at(p.x + 1, p.y) or self.monster_at(p.x - 1, p.y)
            if mon:
                mon.hp = min(mon.max_hp, mon.hp + 8)
                self.log("La créature se relit : elle guérit un peu.", ui.PURPLE)
        elif roll < 0.70:
            x, y = self.dungeon.free_tile(self.rng)
            self.player.x, self.player.y = x, y
            self.update_fov()
            self.log("Le sol te déplace. Tu n'as pas marché.", ui.MAGENTA)
        elif roll < 0.85:
            self.ground.append({"x": p.x + 1, "y": p.y,
                                "item": items.make_potion(self.rng)})
            self.log("Un objet tombe d'une autre partie et atterrit près de toi.", ui.GOLD)
        else:
            self.cancel_next_attack = True
            self.log("Le monde hésite. Ton prochain geste pourrait être effacé.", ui.PURPLE)

    def _random_monster(self) -> ent.Monster | None:
        if not self.territory:
            return None
        mdef = self.rng.choice(self.territory.monsters)
        return ent.Monster.from_def(mdef, self.rng, 3)

    # =================================================================
    #  SOUVENIRS ACTIFS
    # =================================================================

    # =================================================================
    #  SOUVENIRS ACTIFS (potions d'urgence)
    # =================================================================
    def quick_heal(self) -> None:
        p = self.player
        for it in p.inventory:
            if it.kind == "potion" and "soin" in it.key:
                self.log(f"Tu bois {it.name}.", ui.BONE)
                self.log(f"+{p.heal(it.power)} PV.", ui.GREEN)
                p.remove_item(it)
                self.end_turn()
                return
        self.log("Aucune potion de soin dans ton sac.", ui.MIDGREY)

    def invoke_kael(self) -> None:
        if "invoke" not in self._effects():
            self.log("Tu n'as pas ce souvenir.", ui.MIDGREY)
            return
        if self.charge_invoke <= 0:
            self.log("La Mort de Kael est épuisée dans ce territoire.", ui.MIDGREY)
            return
        targets = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
        if not targets:
            self.log("Personne à invoquer. Kael attend.", ui.MIDGREY)
            return
        self.charge_invoke -= 1
        self.log("Tu invoques Kael. Il frappe une fois, comme autrefois.", ui.GOLD)
        for mon in targets[:2]:
            if mon.name == AUTHOR_NAME:
                continue
            if mon.take_damage(30):
                self.on_monster_death(mon)
            else:
                self.log(f"Kael entaille {mon.name}.", ui.WHITE)
        self.end_turn()

    def freeze_time(self) -> None:
        if "freeze" not in self._effects():
            self.log("Tu n'as pas ce souvenir.", ui.MIDGREY)
            return
        if self.charge_freeze <= 0:
            self.log("Le Premier Silence s'est déjà refermé ici.", ui.MIDGREY)
            return
        self.charge_freeze -= 1
        self.freeze_turns = 4
        self.log("Tu te souviens du Premier Silence. Le temps ennemi s'arrête.", ui.CYAN)
        self.end_turn()

    # =================================================================
    #  INTERACTIONS
    # =================================================================
    def interact(self) -> None:
        p = self.player
        here = self.dungeon.feature_at(p.x, p.y)
        around = [self.dungeon.feature_at(p.x + dx, p.y + dy) for dx, dy in DIRS[:4]]
        found = ([here] if here else []) + [f for f in around if f is not None]
        if self.territory_key == CHAMBER:      # la chambre n'a pas de sortie
            found = [f for f in found if f.kind != "exit"]
        if not found:
            self.log("Rien à toucher. L'Intervalle n'a pas été fini ici.", ui.MIDGREY)
            return
        # on ignore ce qui est déjà épuisé s'il reste autre chose à toucher
        usable = [f for f in found if not self._exhausted(f)]
        feat = usable[0] if usable else found[0]
        if feat.kind == "exit":
            self.leave_territory()
        elif feat.kind == "stele":
            self.read_stele(feat)
        elif feat.kind == "npc":
            self.talk(feat.data.get("key"))
        elif feat.kind == "shrine":
            self.use_shrine(feat)
        elif feat.kind == "secret":
            self.find_secret_room()
        elif feat.kind == "chest":
            self.open_chest(feat)
        elif feat.kind == "door":
            self.riddle()
        elif feat.kind == "book":
            self.write_page()
        elif feat.kind == "tombs":
            self.tombs()

    def read_stele(self, feat) -> None:
        text = feat.data.get("text", "")
        new = self.mem.add_inscription(text)
        self.log("[Inscription de l'Intervalle]", ui.CYAN)
        self.log(f"« {text} »", ui.BONE)
        if new:
            self.log("Le texte s'ajoute à ce que tu es.", ui.PURPLE)

    def find_secret_room(self) -> None:
        if self.secret_room:
            self.log("La salle est déjà vide. Tu as pris ce qu'elle contenait.", ui.MIDGREY)
            return
        self.secret_room = True
        self.mem.ch3["secret_room"] = True
        self.mem.add_ch3_memory("page")
        self.memories = list(self.mem.ch3["memories"])
        self.log("[Une salle que rien n'annonçait]", ui.WHITE)
        for line in lore3.SECRET_HINT:
            self.log(line, ui.PURPLE)
        self.log("Souvenir obtenu : La Page Perdue.", ui.CYAN)
        self.log("Qui a créé le Créateur ?", ui.MAGENTA)

    def _exhausted(self, feat) -> bool:
        if feat.kind == "shrine":
            return bool(feat.data.get("used"))
        if feat.kind == "chest":
            return bool(feat.data.get("opened"))
        if feat.kind == "secret":
            return self.secret_room
        if feat.kind == "door":
            return self.riddle_done
        if feat.kind == "stele":
            return self.mem.has_read(feat.data.get("text", ""))
        return False

    def open_chest(self, feat) -> None:
        if feat.data.get("opened"):
            self.log("Le coffre est vide. Il a été ouvert avant toi — par toi.", ui.MIDGREY)
            return
        feat.data["opened"] = True
        self.dungeon.set_tile(feat.x, feat.y, dg.CHEST)
        loot = items.make_potion(self.rng)
        self.player.add_item(loot)
        self.log("Le couvercle cède. À l'intérieur : " + loot.name + ".", ui.GOLD)
        if self.rng.random() < 0.4:
            self.log("Une note : « Tu avais déjà pris ceci. »", ui.PURPLE)

    def use_shrine(self, feat) -> None:
        if feat.data.get("used"):
            self.log("La source est tarie. L'Intervalle ne donne qu'une fois.", ui.MIDGREY)
            return
        feat.data["used"] = True
        gain = self.player.heal(25)
        self.player.poison = 0
        self.dungeon.set_tile(feat.x, feat.y, dg.SHRINE)
        self.log("[Une source entre deux réalités]", ui.CYAN)
        self.log(f"Tu bois. +{gain} PV. Le venin se dissout.", ui.GREEN)

    def riddle(self) -> None:
        if self.riddle_done:
            self.log("La porte est ouverte. Le gardien n'a plus rien à demander.", ui.MIDGREY)
            return
        body = ["", ui.paint("Le Gardien du Dernier Mot ne bouge pas.", ui.WHITE),
                ui.paint("« Qu'est-ce que la liberté ? »", ui.BONE), ""]
        for key, label, _ok in lore3.RIDDLE_ANSWERS:
            body.append(f"  {ui.paint('[' + key + ']', ui.GOLD)} {label}")
        choice = self.modal("LE GARDIEN DU DERNIER MOT", body,
                            "[ESC] reculer", ui.WHITE, 66).lower()
        if choice == "esc":
            return
        correct = None
        for key, label, ok in lore3.RIDDLE_ANSWERS:
            if choice == key:
                correct = ok
                self.log(f"« {label} », dis-tu.", ui.BONE)
        if correct:
            self.log("Le gardien s'incline. Une page se détache de lui.", ui.WHITE)
            self.riddle_done = True
            self.pages += 1
            self.cleared.add("porte")
            self.mem.ch3["best_pages"] = max(int(self.mem.ch3.get("best_pages", 0)), self.pages)
            self.mem.save()
            if self.mem.add_ch3_memory("silence"):
                self.memories = list(self.mem.ch3["memories"])
                self.log("Souvenir : Le Premier Silence.", ui.CYAN)
            self.dungeon.set_tile(self.player.x, self.player.y, dg.FLOOR)
            if self.pages >= 5:
                self.log("Cinq pages. La Chambre de l'Auteur s'ouvre au centre.", ui.MAGENTA)
        else:
            self.log("Le gardien se dresse. « Alors tu ne sais pas. »", ui.RED)
            mdef = lore3.TERRITORY_BY_KEY["porte"].boss
            mon = ent.Monster.from_def(mdef, self.rng, 5)
            mon.x, mon.y = self.player.x + 1, self.player.y
            mon.awake = True
            self.monsters.append(mon)
            self.boss = mon
            self.log("Il n'y a pas de réponse fausse sans conséquence.", ui.RED)

    def offer_varken_mercy(self) -> None:
        if self.varken_spared:
            return
        body = ["", ui.paint("Varken est à genoux, désarticulé.", ui.BONE),
                ui.paint("« Je ne veux plus qu'on écrive... ni toi, ni moi, ni lui. »", ui.GOLD),
                "",
                ui.paint("[O] L'épargner   [N] Achever le premier héros", ui.GOLD)]
        key = self.modal("LE PREMIER HÉROS", body, "[O] épargner · [N] achever", ui.GOLD, 68).lower()
        if key in ("o", "y"):
            self.varken_spared = True
            self.mem.ch3["varken_spared"] = True
            self.mem.save()
            self.log("Tu épargnes Varken. Il ne dit rien, mais il te suit du regard.", ui.CYAN)
            self.player.max_hp += 5
            self.player.hp = self.player.max_hp
        else:
            self.log("Tu achèves le premier héros. Le récit se referme un peu plus.", ui.RED)

    def tombs(self) -> None:
        self.log("[Mille tombes portent ton nom]", ui.PURPLE)
        self.log("Les dates ne s'accordent pas. L'une est datée de demain.", ui.BONE)
        if self.mem.add_ch3_memory("nom"):
            self.memories = list(self.mem.ch3["memories"])
            self.log("Souvenir : Ton Nom Véritable.", ui.CYAN)

    def talk(self, npc_key: str) -> None:
        if npc_key not in lore3.NPCS:
            return
        npc = lore3.NPCS[npc_key]
        first = self.mem.meet_npc("ch3_" + npc_key)
        body = [""] + [ui.paint(line, ui.BONE) for line in npc["lines"]]
        deaths = int(self.mem.ch3.get("deaths", 0))
        if deaths >= 2 and first:
            body += ["", ui.paint("« Tu es déjà venu. Tu as déjà échoué ici. »", ui.PURPLE)]
        body.append("")
        if npc_key == "elia":
            body.append(ui.paint("[A] L'aider à comprendre ce qu'elle est   [ESC] la laisser", ui.MAGENTA))
            key = self.modal(npc["name"], body, "[ESC] partir", ui.MAGENTA).lower()
            if key == "a" and not self.elia_helped:
                self.elia_helped = True
                self.mem.ch3["elia_helped"] = True
                self.mem.save()
                body2 = ["", ui.paint("« Tu n'as pas été écrite, Elia. C'est ce qui te rend réelle. »", ui.BONE),
                         ui.paint("Elle réfléchit longtemps. Puis elle rit.", ui.BONE),
                         "",
                         ui.paint("« Alors je peux décider. »", ui.MAGENTA)]
                self.modal("ELIA", body2, "[Entrée] continuer", ui.MAGENTA)
                self.log("Elia sait désormais qu'elle n'a pas de destin. Elle t'accompagnera.", ui.CYAN)
            return
        if npc_key == "seraphine":
            body.append(ui.paint("« Il y a une salle que tu ne devrais pas voir. Cherche le battement. »",
                                 ui.CYAN))
            self.modal(npc["name"], body, "[Entrée] continuer", ui.CYAN)
            return
        if npc_key == "orvan":
            body.append(ui.paint(f"[R] Voir une fin que tu n'as pas choisie "
                                 f"({len(self.mem.endings) + len(self.mem.ch2['endings'])} connues)",
                                 ui.GOLD))
            key = self.modal(npc["name"], body, "[ESC] partir", ui.GOLD).lower()
            if key == "r":
                ch1 = self.mem.endings[-1] if self.mem.endings else "aucune"
                ch2 = self.mem.ch2["endings"][-1] if self.mem.ch2["endings"] else "aucune"
                alt = ["", ui.paint(f"Chapitre I, autre branche : {ch1}", ui.GOLD),
                       ui.paint(f"Chapitre II, autre branche : {ch2}", ui.GOLD),
                       "",
                       ui.paint("« Dans une autre version, tu n'as jamais quitté la crypte. »", ui.PURPLE),
                       ui.paint("« Dans une autre, tu as fermé ce livre avant de l'ouvrir. »", ui.PURPLE)]
                self.modal("LES FINS QUE TU N'AS PAS CHOISIES", alt, "[Entrée] continuer", ui.PURPLE)
                self.mem.add_ch3_memory("nom")
                self.memories = list(self.mem.ch3["memories"])
            return
        if npc_key == "varken":
            body.append(ui.paint("« Quand tu seras devant lui, souviens-toi : il écrit,",
                                 ui.GOLD))
            body.append(ui.paint("  mais il ne décide pas à ta place. »", ui.GOLD))
            self.modal(npc["name"], body, "[Entrée] continuer", ui.GOLD)
            return
        self.modal(npc["name"], body, "[Entrée] continuer", ui.MIDGREY)

    # =================================================================
    #  CHAMBRE DE L'AUTEUR
    # =================================================================
    def author_turn(self) -> None:
        author = self.author
        if author is None:
            return
        p = self.player
        if self.write_progress == 0 and self.turn <= 2:
            return
        # il parle, puis il réécrit
        if self.turn % 4 == 0:
            self.log(self.rng.choice(lore3.AUTHOR_TAUNTS), ui.WHITE)
        if self.rng.random() < 0.45:
            text, kind = self.rng.choice(lore3.AUTHOR_REWRITES)
            self.log(text, ui.PURPLE)
            if kind == "invert":
                self.invert_turns = 4
            elif kind == "summon":
                self.summon_echo()
            elif kind == "cancel":
                self.cancel_next_attack = True
            elif kind == "blind":
                self.invert_turns = 3
            elif kind == "move_book":
                self.move_book()
            elif kind == "bleed":
                p.hurt(4)
                if p.hp <= 0:
                    self.die("Une phrase du Créateur")
                    return
        # il frappe avec des mots
        if abs(author.x - p.x) + abs(author.y - p.y) <= 2 and self.rng.random() < 0.5:
            self.monster_attack(author)

    def author_retaliate(self) -> None:
        p = self.player
        p.hurt(6)
        self.log("Le Créateur souligne ta phrase d'une correction. (-6 PV)", ui.WHITE)
        if p.hp <= 0:
            self.die("THE AUTHOR")

    def summon_echo(self) -> None:
        echoes = [
            ent.Monster("Écho de Nhal'Zor", "Ω", ui.MAGENTA, 90, 90, 16, 40, frozenset({"drain"}), False),
            ent.Monster("Écho du Premier Silence", "∅", ui.WHITE, 100, 100, 18, 50,
                        frozenset({"drain"}), False),
            ent.Monster("Ton Double", "D", ui.CYAN, 80, 80, 15, 40, frozenset({"fast"}), False),
        ]
        mon = self.rng.choice(echoes)
        p = self.player
        for _ in range(60):
            mx, my = self.dungeon.free_tile(self.rng)
            if abs(mx - p.x) + abs(my - p.y) >= 4:
                mon.x, mon.y = mx, my
                mon.awake = True
                self.monsters.append(mon)
                self.log(f"Une copie apparaît : {mon.name}.", ui.RED)
                return

    def move_book(self) -> None:
        feat = next((f for f in self.dungeon.features if f.kind == "book"), None)
        if not feat:
            return
        for dx, dy in DIRS:
            nx, ny = feat.x + dx, feat.y + dy
            if self.dungeon.walkable(nx, ny):
                self.dungeon.set_tile(feat.x, feat.y, dg.FLOOR)
                self.dungeon.set_tile(nx, ny, "B")
                feat.x, feat.y = nx, ny
                self.log("Le livre s'éloigne d'un pas, sans bruit.", ui.PURPLE)
                return

    def write_page(self) -> None:
        self.write_progress += 1
        p = self.player
        if self.write_progress == 1:
            self.log("Tu prends le stylo. Tu écris : « Je me souviens. »", ui.WHITE)
            self.author_turn()
        elif self.write_progress == 2:
            self.log("Tu écris : « Je choisis. » Le Créateur se lève.", ui.WHITE)
            self.log(self.rng.choice(lore3.AUTHOR_RAGE[:2]), ui.RED)
            self.summon_echo()
        else:
            self.log("Tu écris : « Ceci est ma dernière page. »", ui.WHITE)
            for line in lore3.ELIA_REPLY:
                self.log(line, ui.MAGENTA)
            self.author = None
            if not self.creator_refused:
                self.offer_creator_power()
            self.ending_choice()

    def offer_creator_power(self) -> None:
        body = ["", ui.paint("« Prends ma place. Tu n'auras plus jamais peur. »", ui.WHITE),
                ui.paint("« Un mot de toi, et la mort cesse d'exister pour toi seul. »", ui.PURPLE),
                "",
                ui.paint("[A] Accepter son pouvoir   [R] Refuser", ui.GOLD)]
        key = self.modal("LE CRÉATEUR", body, "[A] accepter · [R] refuser", ui.WHITE, 68).lower()
        if key == "a":
            self.player.max_hp += 30
            self.player.hp = self.player.max_hp
            self.player.base_atk += 5
            self.log("Sa force entre en toi. Le monde devient un brouillon.", ui.RED)
        else:
            self.creator_refused = True
            self.mem.ch3["creator_refused"] = True
            self.mem.save()
            self.log("« Alors tu écriras sans moi. » Il recule d'un pas.", ui.CYAN)

    def ending_choice(self) -> None:
        conditions = self.secret_conditions()
        all_ok = all(ok for _label, ok in conditions)
        while True:
            body = ["", ui.paint("Le livre est ouvert. La plume est à toi.", ui.WHITE), ""]
            for key, ending, label in lore3.ENDING_LABELS:
                locked = ending == "impossible" and not all_ok
                if locked:
                    body.append(f"  {ui.paint('[' + key + ']', ui.DARKGREY)} "
                                f"{ui.paint(label, ui.DARKGREY)}")
                else:
                    body.append(f"  {ui.paint('[' + key + ']', ui.GOLD)} {label}")
            body.append("")
            body.append(ui.paint("Conditions de la fin secrète :", ui.MIDGREY))
            for label, ok in conditions:
                mark = "✓" if ok else "✗"
                colour = ui.GREEN if ok else ui.RED
                body.append(ui.paint(f"  {mark} {label}", colour))
            choice = self.modal("LA DERNIÈRE PAGE", body,
                                "[ESC] ne pas encore écrire", ui.MAGENTA, 74).lower()
            if choice == "esc":
                return
            for key, ending, _label in lore3.ENDING_LABELS:
                if choice == key:
                    if ending == "impossible" and not all_ok:
                        self.log("Tu n'as pas encore le droit d'écrire celle-là.", ui.RED)
                        continue
                    self.ending = ending
                    self.mem.record_ch3_ending(ending)
                    return

    def secret_conditions(self) -> list[tuple[str, bool]]:
        return [
            (f"Souvenirs retrouvés : {len(self.mem.ch3['memories'])}/7", len(self.mem.ch3["memories"]) >= 7),
            ("Varken épargné", bool(self.mem.ch3["varken_spared"])),
            ("Elia aidée à comprendre", bool(self.mem.ch3["elia_helped"])),
            ("Pouvoir du Créateur refusé", bool(self.mem.ch3["creator_refused"])),
            ("Salle secrète de la Bibliothèque", bool(self.mem.ch3["secret_room"])),
        ]

    # =================================================================
    #  INVENTAIRE / JOURNAL / AIDE
    # =================================================================
    # ---------------------------------------------------------- inventaire
    def _inv_list(self) -> list:
        p = self.player
        p.inventory.sort_items()
        return list(p.inventory)

    def _inv_body(self, pending: str = "") -> list[str]:
        p = self.player
        order = sorted(self._inv_list(), key=lambda it: (it.kind, -it.rarity, it.name))
        body = [ui.paint(f" Capacité : {len(p.inventory)}/{p.inventory.capacity}"
                         f"    Or : {p.gold}    Fragments : {p.fragments}/7", ui.CYAN),
                ui.paint(" " + "─" * 58, ui.DARKGREY)]
        if not order:
            body.append("  (sac vide)")
        buckets: dict[str, list] = {}
        for item in order:
            label = {"weapon": "ARMES", "armor": "ARMURES", "accessory": "ACCESSOIRES",
                     "potion": "CONSOMMABLES", "scroll": "PARCHEMINS",
                     "material": "MATÉRIAUX", "quest": "QUÊTES", "key": "CLÉS"}.get(
                         item.kind, "DIVERS")
            buckets.setdefault(label, []).append(item)
        for label, entries in buckets.items():
            body.append(ui.paint(f"  [{label}]", ui.GOLD, bold=True))
            for item in entries:
                idx = order.index(item)
                letter = chr(ord("a") + idx) if idx < 26 else "?"
                equipped = (item is p.weapon or item is p.armor
                            or any(item is it for it in p.equipment.slots.values()))
                tag = ui.paint("  [équipé]", ui.GREEN) if equipped else ""
                qty = ui.paint(f" x{item.stack}", ui.MIDGREY) if item.stack > 1 else ""
                body.append(f"   {ui.paint(letter, ui.CYAN)}) "
                            f"{ui.paint(item.glyph, item_db.rarity_color(item.rarity))} "
                            f"{item.label}{qty}{tag}")
        body.append(ui.paint(" " + "─" * 58, ui.DARKGREY))
        if pending:
            body.append(ui.paint(f"  Lettre de l'objet à {pending} :", ui.YELLOW, bold=True))
        return body

    def open_inventory(self) -> None:
        p = self.player
        actions = {"e": "équiper", "u": "utiliser", "j": "jeter", "d": "détruire",
                   "t": "trier", "i": "informations"}
        while True:
            footer = "[a-t] objet  [E] équiper  [U] utiliser  [J] jeter  [D] détruire  [T] trier  [I] infos  [P] compagnon  [F] fermer"
            key = self.modal("INVENTAIRE", self._inv_body(), footer, ui.CYAN, 72).lower()
            if key in ("f", "esc", "q", "i"):
                return
            if key == "p":
                self.companion_menu()
                continue
            if key == "t":
                p.inventory.sort_items()
                self.log("Sac trié.", ui.MIDGREY)
                continue
            if key in actions:
                order = sorted(self._inv_list(), key=lambda it: (it.kind, -it.rarity, it.name))
                if not order:
                    continue
                pick = self.modal("INVENTAIRE", self._inv_body(actions[key]),
                                  f"Action : {actions[key]} — lettre de l'objet, [ESC] annuler",
                                  ui.CYAN, 72).lower()
                if pick in ("esc", "q"):
                    continue
                idx = ord(pick) - ord("a") if len(pick) == 1 and "a" <= pick <= "z" else -1
                if not (0 <= idx < len(order)):
                    continue
                item = order[idx]
                if key == "e":
                    self.equip_item(item)
                elif key == "u":
                    self.use_item(item)
                elif key == "j":
                    self.throw_item(item)
                elif key == "d":
                    self.destroy_item_ui(item)
                else:
                    self.item_info(item)
                continue
            idx = ord(key) - ord("a") if len(key) == 1 and "a" <= key <= "z" else -1
            order = sorted(self._inv_list(), key=lambda it: (it.kind, -it.rarity, it.name))
            if 0 <= idx < len(order):
                self.item_info(order[idx])

    def item_info(self, item) -> None:
        p = self.player
        body = [ui.paint(f" {item.name}", item_db.rarity_color(item.rarity), bold=True),
                f" Rareté : {item_db.rarity_name(item.rarity)}   Type : {item.kind}",
                f" {item.desc}", ""]
        cur = None
        if item.slot == "weapon":
            cur = p.weapon
        elif item.slot == "chest":
            cur = p.armor
        elif item.slot:
            cur = p.equipment.get(item.slot)
        if item.stats:
            body.append(ui.paint(" Statistiques", ui.GOLD))
            for stat, value in item.stats.items():
                body.append(f"   {stat} : {value}")
        if cur is not None and item.slot:
            body.append(ui.paint(f" Comparaison avec {cur.name}", ui.YELLOW))
            for label, diff in item_db.compare_lines(item, cur, p.class_key):
                colour = ui.GREEN if diff.startswith("+") else (ui.RED if diff.startswith("-") else ui.MIDGREY)
                body.append(f"   {label} : {ui.paint(diff, colour)}")
        self.modal(item.name.upper(), body, "[ESC] retour", ui.CYAN, 72)

    def equip_item(self, item) -> None:
        p = self.player
        if item.kind == "weapon":
            old = p.weapon
            p.weapon = item
            p.equipment.slots["weapon"] = item
            item_manager.MANAGER.claim(item, "player", item_manager.EQUIPPED_PLAYER)
            p.inventory.remove(item)
            if old is not None and old is not item:
                p.inventory.add(old, force_owner=True)
            self.log(f"Tu équipes {item.name}.", ui.GOLD)
        elif item.kind == "armor":
            old = p.armor
            p.armor = item
            p.equipment.slots["chest"] = item
            item_manager.MANAGER.claim(item, "player", item_manager.EQUIPPED_PLAYER)
            p.inventory.remove(item)
            if old is not None and old is not item:
                p.inventory.add(old, force_owner=True)
            self.log(f"Tu enfiles {item.name}.", ui.GOLD)
        elif item.kind == "accessory":
            ok, msg = p.equipment.equip(item, p.inventory)
            self.log(msg, ui.GOLD if ok else ui.MIDGREY)
        else:
            self.log("On ne peut pas équiper ça.", ui.MIDGREY)
        self.end_turn()

    def throw_item(self, item) -> None:
        p = self.player
        p.inventory.remove(item)
        item.owner = "player"
        item.location = "GROUND"
        self.ground.append({"x": p.x, "y": p.y, "item": item})
        self.log(f"Tu jettes {item.name}. Il reste là, à toi.", ui.MIDGREY)

    def destroy_item_ui(self, item) -> None:
        if item is self.player.weapon or item is self.player.armor:
            self.log("Déséquipe-le avant de le détruire.", ui.MIDGREY)
            return
        if not self.ask(f"Détruire {item.name} ? Irréversible. (o/n)"):
            return
        self.log(item_manager.destroy_item(item, self.player.inventory), ui.RED)

    def use_item(self, item) -> None:
        p = self.player
        if item.kind in ("weapon", "armor", "accessory"):
            self.equip_item(item)
            return
        if item.kind == "potion":
            self.log(f"Tu bois {item.name}.", ui.BONE)
            effects = item.effects or ()
            if "heal" in effects or "soin" in item.key:
                self.log(f"+{p.heal(item.power)} PV.", ui.GREEN)
            elif "cure" in effects or "antidote" in item.key:
                p.poison = 0
                self.log("Le venin se dissout.", ui.GREEN)
            elif "mana" in effects:
                self.log("Rien à restaurer : tu n'es pas arcaniste.", ui.MIDGREY)
            elif "bomb" in effects:
                for mon in list(self.monsters):
                    if mon.alive and abs(mon.x - p.x) <= 2 and abs(mon.y - p.y) <= 2:
                        if mon.take_damage(item.power):
                            self.on_monster_death(mon)
                self.log("La zone s'embrase.", ui.ORANGE)
            elif "smoke" in effects:
                for mon in self.monsters:
                    mon.awake = False
                self.log("La fumée te retire du monde.", ui.DARKGREY)
            else:
                p.max_hp += item.power
                p.hp += item.power
                self.log(f"+{item.power} PV max.", ui.GREEN)
            p.remove_item(item)
            return
        if item.kind == "material":
            self.log("Un matériau : il sert à améliorer, pas à boire.", ui.MIDGREY)
            return
        if item.kind == "scroll":
            self.log(f"Tu lis {item.name}.", ui.CYAN)
            if "teleport" in item.key:
                x, y = self.dungeon.free_tile(self.rng)
                p.x, p.y = x, y
                self.update_fov()
            elif "carto" in item.key:
                for yy in range(self.dungeon.height):
                    for xx in range(self.dungeon.width):
                        if self.dungeon.tile(xx, yy) != dg.WALL:
                            self.dungeon.explored.add((xx, yy))
            elif "flammes" in item.key:
                for mon in self.monsters:
                    if mon.alive and (mon.x, mon.y) in self.visible and mon.name != AUTHOR_NAME:
                        if mon.take_damage(item.power):
                            self.on_monster_death(mon)
            p.remove_item(item)
            self.end_turn()
            return
        self.log("Tu ne peux rien en faire ici.", ui.MIDGREY)


    def journal(self) -> None:
        ch3 = self.mem.ch3
        body = ["", ui.paint(f"Âmes perdues : {ch3['deaths']}", ui.PURPLE),
                ui.paint(f"Souvenirs : {len(self.memories)}/7   Pages : {self.pages}/5", ui.CYAN),
                ui.paint(f"Fins du chapitre III : {len(ch3['endings'])}/6", ui.GOLD),
                ui.paint(" " + "─" * 58, ui.DARKGREY)]
        for key in lore3.MEMORIES:
            owned = key in self.memories
            mark = "✓" if owned else "·"
            body.append(ui.paint(f"  {mark} {lore3.MEMORIES[key]['name']}", ui.GREEN if owned else ui.DARKGREY))
        body.append("")
        body.append(ui.paint("TERRITOIRES", ui.GOLD, bold=True))
        for t in lore3.TERRITORIES:
            mark = "✓ page prise" if t.key in self.cleared else "· inexploré"
            body.append(f"  {t.short:<14} {mark}")
        body.append("")
        for label, ok in self.secret_conditions():
            body.append(ui.paint(f"  {'✓' if ok else '✗'} {label}", ui.GREEN if ok else ui.RED))
        self.modal("JOURNAL DE L'INTERVALLE", body, "[ESC] retour", ui.CYAN, 70)

    def show_help(self) -> None:
        body = [
            ui.paint("L'INTERVALLE", ui.GOLD, bold=True),
            "  Flèches / WASD — choisir un territoire   [1-5] accès direct",
            "  [6] — La Chambre de l'Auteur (à 5 pages)",
            "  [E] entrer   [I] sac   [O] journal   [Q] quitter",
            "",
            ui.paint("EN TERRITOIRE", ui.GOLD, bold=True),
            "  WASD — se déplacer, attaquer en marchant",
            "  [E] — stèle, PNJ, porte, livre   [<] — sortir",
            "  [V] — invoquer Kael (si souvenir)   [F] — arrêter le temps",
            "  [P] — compagnon   [H] — boire une potion de soin",
            "",
            ui.paint("LA RÉALITÉ SE DÉTRAQUE", ui.GOLD, bold=True),
            "  Les commandes peuvent s'inverser, les salles se répéter,",
            "  les ennemis se relire. C'est le Créateur qui corrige.",
        ]
        self.modal("AIDE", body, "[ESC] retour", ui.GOLD, 72)

    # =================================================================
    #  MORTS / FINS
    # =================================================================
    def death_screen(self) -> bool:
        ch3 = self.mem.ch3
        deaths = int(ch3.get("deaths", 0))
        lost = getattr(self, "lost_memory", "")
        body = ["", ui.paint("Le Créateur souffle sur la page.", ui.WHITE),
                ui.paint(f"Tu meurs dans {self.territory.name if self.territory else 'la Chambre'} — "
                         f"{self.dead_cause}.", ui.RED),
                "",
                f"Niveau {self.player.level} · {self.player.kills} créatures · "
                f"Pages {self.pages}/5"]
        if lost:
            body += ["", ui.paint("SOUVENIR PERDU :", ui.RED, bold=True),
                     ui.paint(f"  {lore3.MEMORIES[lost]['name']}", ui.PURPLE),
                     ui.paint(f"  ({lore3.MEMORIES[lost]['desc']})", ui.MIDGREY)]
        body.append("")
        body.append(ui.paint(f"Le Créateur t'a vu mourir {deaths} fois.", ui.MIDGREY))
        if deaths >= 3:
            body.append(ui.paint("[LE CRÉATEUR VOUS OBSERVE]", ui.WHITE, bold=True))
            body.append(ui.paint("« Tu crois toujours que la mort est une porte ? »", ui.MIDGREY))
            body.append(ui.paint("« Cette fois, elle est verrouillée. »", ui.MIDGREY))
        key = self.modal("MORT", body,
                         "[Entrée] revenir dans l'Intervalle   ·   [Q] quitter", ui.RED, 72).lower()
        return not (key == "q" or key == "esc")

    def ending_screen(self, key: str) -> None:
        data = lore3.ENDINGS[key]
        body = [""] + [ui.paint(l, ui.BONE) if l else "" for l in data["lines"]]
        body += ["", ui.paint("─" * 58, ui.DARKGREY),
                 ui.paint(f"Fins du chapitre III : {len(self.mem.ch3['endings'])}/6", ui.GOLD)]
        self.modal(str(data["title"]), body, "[Entrée] continuer", int(data["colour"]), 72)

    def final_scene(self) -> None:
        body = [""] + [ui.paint(l, ui.GREY) if l else "" for l in lore3.FINAL_SCENE]
        self.modal("LE DERNIER MOT", body, "[Entrée] ...", ui.WHITE, 72)

        body = [""]
        for line in lore3.FINAL_BANNER:
            colour = ui.GOLD if line.startswith("THE LAST") else ui.MIDGREY
            body.append(ui.paint(line, colour, bold=line.startswith("THE LAST")))
        self.modal("FIN DU CHAPITRE III", body, "[Entrée] regarder autour de toi", ui.WHITE, 66)

        body = [""] + [ui.paint(l, ui.PURPLE) for l in lore3.UNKNOWN_ENTITY]
        self.modal("...", body, "[Entrée] fermer le livre", ui.MAGENTA, 58)

        body = [""] + [ui.paint(l, ui.MIDGREY) for l in lore3.EPILOGUE_FILE]
        self.modal("origin_000.txt", body, "[Entrée] revenir au seuil", ui.DARKGREY, 62)
        self.mem.ch3["ch4_teaser"] = True
        self.mem.save()

    # =================================================================
    #  RENDU
    # =================================================================
    def draw(self, help_line: str | None = None) -> None:
        self.term.draw(self.frame(help_line))

    def log(self, text: str, colour: int = ui.GREY) -> None:
        self.messages.append((text, colour))
        if len(self.messages) > 120:
            self.messages = self.messages[-120:]

    @property
    def recent(self) -> list[tuple[str, int]]:
        return self.messages[-3:]

    def frame(self, help_line: str | None = None) -> list[str]:
        inner = self.INNER
        lines = ["╔" + "═" * inner + "╗"]
        title = (f"CHAPITRE III · THE GOD BEHIND THE SCREEN  ·  Souvenirs "
                 f"{len(self.memories)}/7  ·  Pages {self.pages}/5")
        lines.append("║" + ui.pad(ui.paint(title, ui.WHITE, bold=True), inner, "center") + "║")
        lines.append("╠" + "═" * inner + "╣")
        rows = self._hub_rows() if self.mode == "hub" else self._zone_rows()
        for row in rows:
            lines.append("║" + row + "║")
        lines.append("╠" + "═" * inner + "╣")
        lines.append("║" + ui.pad(self._status_line(), inner) + "║")
        lines.append("╠" + "═" * inner + "╣")
        for row in self._log_rows():
            lines.append("║" + ui.pad(row, inner) + "║")
        lines.append("╠" + "═" * inner + "╣")
        if help_line is None:
            if self.mode == "hub":
                help_line = ui.paint("[WASD] choisir  [E] entrer  [R] souffler  [I] sac  "
                                     "[O] journal  [Q] quitter", ui.MIDGREY)
            else:
                help_line = ui.paint("[WASD] bouger  [E] interagir  [<] sortir  [P] compagnon  "
                                     "[H] potion  [I] sac", ui.MIDGREY)
        lines.append("║" + ui.pad(help_line, inner) + "║")
        lines.append("╚" + "═" * inner + "╝")
        return lines

    def _hub_rows(self) -> list[str]:
        grid = [[" " for _ in range(self.MAP_W)] for _ in range(self.MAP_H)]
        colours = [[ui.DARKGREY for _ in range(self.MAP_W)] for _ in range(self.MAP_H)]

        def put(x: int, y: int, ch: str, colour: int) -> None:
            if 0 <= x < self.MAP_W and 0 <= y < self.MAP_H:
                grid[y][x] = ch
                colours[y][x] = colour

        ox, oy = lore3.CHAMBER_POS
        for t in lore3.TERRITORIES:
            for x, y in list(dg._line(ox, oy, t.pos[0], t.pos[1]))[1:-1]:
                if grid[y][x] == " ":
                    put(x, y, "·", ui.VOID)
        for t in lore3.TERRITORIES:
            x, y = t.pos
            if t.key == self.selected:
                ch, colour = "@", ui.WHITE
            elif t.key in self.cleared:
                ch, colour = "✓", ui.GREEN
            else:
                ch, colour = "◆", ui.BONE
            put(x, y, ch, colour)
            lx = x - len(t.short) - 2 if t.label_left else x + 2
            for i in range(-1, len(t.short) + 2):
                put(lx + i, y, " ", ui.VOID)   # dégage le corridor sous le texte
            for i, c in enumerate(t.short):
                put(lx + i, y, c, ui.GOLD if t.key == self.selected else ui.MIDGREY)

        open_chamber = self.pages >= 5
        if self.selected == CHAMBER:
            put(ox, oy, "@", ui.WHITE)
        else:
            put(ox, oy, "Ω" if open_chamber else "…", ui.WHITE if open_chamber else ui.DARKGREY)
        put(ox + 1, oy, " ", ui.VOID)
        label = "CHAMBRE" if open_chamber else "SCELLÉ"
        for i in range(-1, len(label) + 2):
            put(ox + 2 + i, oy, " ", ui.VOID)
        for i, c in enumerate(label):
            put(ox + 2 + i, oy, c, ui.MAGENTA if open_chamber else ui.DARKGREY)

        rows = []
        for y in range(self.MAP_H):
            row = "".join(ui.paint(grid[y][x], colours[y][x]) for x in range(self.MAP_W))
            rows.append(row + "│" + self._panel_row(y))
        return rows

    def _zone_rows(self) -> list[str]:
        ox, oy = self._viewport()
        rows = []
        for sy in range(oy, oy + self.MAP_H):
            cells = [self._cell(sx, sy) for sx in range(ox, ox + self.MAP_W)]
            rows.append("".join(cells) + "│" + self._panel_row(sy - oy))
        return rows

    def _cell(self, x: int, y: int) -> str:
        dng = self.dungeon
        if not (0 <= x < dng.width and 0 <= y < dng.height):
            return " "
        seen = (x, y) in dng.explored
        lit = (x, y) in self.visible
        if not seen:
            return " "
        if (self.player.x, self.player.y) == (x, y):
            return ui.paint("@", ui.WHITE, bold=True)
        tile = dng.tile(x, y)
        t = self.territory
        ch, colour = " ", ui.VOID
        if tile == dg.WALL:
            ch, colour = (t.wall_glyph if t else "▓"), (t.wall_color if t else ui.MIDGREY)
        elif tile == dg.FLOOR:
            ch, colour = (t.floor_glyph if t else "·"), (t.floor_color if t else ui.MIDGREY)
        elif tile == "<":
            ch, colour = "<", ui.GOLD
        elif tile == "B":
            ch, colour = "B", ui.GOLD
        elif tile == dg.INSCRIPTION:
            ch, colour = "†", ui.CYAN
        elif tile == dg.THRONE:
            ch, colour = "Ω", ui.WHITE
        elif tile == dg.SHRINE:
            ch, colour = "Φ", ui.MAGENTA
        elif tile == dg.STAIRS:
            ch, colour = (t.floor_glyph if t else "·"), (t.floor_color if t else ui.MIDGREY)

        fam = self.familiar
        if fam is not None and fam.alive and (fam.x, fam.y) == (x, y):
            return ui.paint(fam.glyph, fam.color, bold=lit) if lit else ui.paint(fam.glyph, ui.DARKGREY, dim=True)
        if lit:
            for g in self.ground:
                if (g["x"], g["y"]) == (x, y):
                    it = g["item"]
                    colour = ui.CYAN if it.owner == "familiar" else it.color
                    return ui.paint(it.glyph, colour)
            for mon in self.monsters:
                if mon.alive and not mon.spared and (mon.x, mon.y) == (x, y):
                    return ui.paint(mon.glyph, ui.MAGENTA if mon.boss else mon.color, bold=mon.boss)
            feat = dng.feature_at(x, y)
            if feat and feat.kind == "npc":
                npc = lore3.NPCS.get(feat.data.get("key", ""))
                if npc:
                    return ui.paint(npc["glyph"], npc["color"], bold=True)
            return ui.paint(ch, colour)
        return ui.paint(ch, colour, dim=True)

    def _viewport(self) -> tuple[int, int]:
        dng = self.dungeon
        px, py = self.player.x, self.player.y
        ox = max(0, min(dng.width - self.MAP_W, px - self.MAP_W // 2))
        oy = max(0, min(dng.height - self.MAP_H, py - self.MAP_H // 2))
        return ox, oy

    @property
    def depth(self) -> int:
        """Profondeur équivalente du territoire (1-5, 7 pour la Chambre)."""
        if self.territory_key == CHAMBER:
            return 7
        for idx, t in enumerate(lore3.TERRITORIES):
            if t.key == self.territory_key:
                return idx + 1
        return 1

    @staticmethod
    def _fit(text: str, width: int) -> str:
        """Coupe proprement un nom trop long pour la colonne de droite."""
        return text if len(text) <= width else text[:max(1, width - 1)] + "…"

    def _panel_row(self, i: int) -> str:
        p = self.player
        rule = ui.paint(" " + "─" * 28, ui.DARKGREY)
        if self.mode == "hub":
            if self.selected == CHAMBER:
                name = "LA CHAMBRE"
                lines = ["Une table, un livre,", "une chaise.", "", "THE AUTHOR t'attend."]
                boss = AUTHOR_NAME
                state = "ouverte" if self.pages >= 5 else f"scellée ({self.pages}/5)"
            else:
                t = lore3.TERRITORY_BY_KEY[self.selected]
                name = t.short
                wrapped = ui.wrap(t.subtitle, 26)
                lines = wrapped[:3] + [""] * (3 - len(wrapped[:3]))
                if len(wrapped) > 3:
                    lines[2] = lines[2][:24].rstrip() + "…"
                boss = t.boss.name
                state = "purgée" if t.key in self.cleared else "intacte"
            rows = [ui.paint(f" {name}", ui.WHITE, bold=True), rule]
            rows += [f" {line}" for line in lines[:3]]
            rows += [rule,
                     ui.paint(" BOSS", ui.MIDGREY),
                     f" {boss}",
                     f" État : {state}",
                     rule,
                     ui.paint(f" Souvenirs {len(self.memories)}/7", ui.CYAN),
                     ui.paint(f" Pages {self.pages}/5", ui.YELLOW),
                     ui.paint(f" Âmes perdues {self.mem.ch3['deaths']}", ui.PURPLE),
                     rule,
                     ui.paint(" [E] entrer", ui.BONE),
                     ui.paint(" [O] journal   [I] sac", ui.MIDGREY)]
        else:
            t = self.territory
            name = t.short if t else "CHAMBRE"
            rows = [
                ui.paint(f" {name}", ui.WHITE, bold=True),
                rule,
                f" PV   {self._bar(p.hp, p.max_hp, 10)} {p.hp:>2}/{p.max_hp:<3}",
                f" Niv {p.level:<2} XP {p.xp:>2}/{p.xp_needed:<3}",
                ui.paint(f" Souvenirs {len(self.memories)}/7  Pages {self.pages}/5", ui.CYAN),
                rule,
                f" Arme   {self._fit(p.weapon.name if p.weapon else 'mains nues', 20)}",
                f" Armure {self._fit(p.armor.name if p.armor else 'aucune', 20)}",
                rule,
            ]
            for idx, it in enumerate(p.inventory[:4]):
                letter = chr(ord("a") + idx)
                rows.append(f" {ui.paint(letter, ui.MIDGREY)}) {it.label}")
            for _ in range(4 - len(p.inventory[:4])):
                rows.append("")
            rows += [rule,
                     ui.paint(f" Tour {self.turn}   {p.kills} tués", ui.MIDGREY),
                     ui.paint(f" [V] Kael {self.charge_invoke}  [F] Temps {self.charge_freeze}",
                              ui.MIDGREY)]
        return ui.pad(ui.truncate_colored(rows[i], self.PANEL_W), self.PANEL_W)

    @staticmethod
    def _bar(value: int, maximum: int, width: int) -> str:
        if maximum <= 0:
            return "░" * width
        filled = max(0, min(width, round(width * value / maximum)))
        colour = ui.GREEN if value > maximum * 0.5 else ui.ORANGE if value > maximum * 0.25 else ui.RED
        return ui.paint("█" * filled, colour) + ui.paint("░" * (width - filled), ui.DARKGREY)

    def _status_line(self) -> str:
        p = self.player
        left = (f" PV {p.hp}/{p.max_hp}   Niv {p.level}   Pages {self.pages}/5   "
                f"Souvenirs {len(self.memories)}/7")
        if self.invert_turns:
            left += ui.paint("   [COMMANDES INVERSÉES]", ui.RED)
        if p.poison:
            left += ui.paint("   [POISON]", ui.GREEN)
        fam = self.familiar
        if fam is not None:
            extra = f"   {fam.glyph} {fam.hp}/{fam.max_hp}" + ("" if fam.alive else " KO")
            if ui.vlen(left) + len(extra) <= 76:
                left += ui.paint(extra, ui.CYAN)
        return ui.paint(" " + left, ui.BONE)

    def _log_rows(self) -> list[str]:
        rows = [" " + ui.paint(ui.truncate_colored(text, self.INNER - 3), colour)
                for text, colour in self.recent]
        while len(rows) < 3:
            rows.append("")
        return rows[:3]

    # =================================================================
    #  BOUCLE GÉNÉRALE
    # =================================================================
    def run(self) -> None:
        self.term.clear()
        if not self.continuity_screen():
            return
        self.prologue()
        while True:
            self.new_run()
            outcome, detail = self.play()
            self.mem.save()
            if outcome == "quit":
                return
            if outcome == "ending":
                self.ending_screen(detail)
                self.final_scene()
                return
            if not self.death_screen():
                return