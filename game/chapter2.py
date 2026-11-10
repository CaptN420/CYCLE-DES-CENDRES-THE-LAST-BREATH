"""CHAPITRE II — LE ROYAUME DES ÂMES BRISÉES : boucle de jeu complète."""
from __future__ import annotations

import math
import random

from . import dungeon as dg
from . import entities as ent
from . import familiar_field, items, lore2, loot_manager, ui

KEYMAP = {
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
    "k": (0, -1), "j": (0, 1), "h": (-1, 0), "l": (1, 0),
    "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1),
    "UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0),
}

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]

ORIGIN = "origin"
ORIGIN_POS = (20, 7)


class Chapter2(familiar_field.FamiliarField):
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
        self.mode = "world"            # world | region
        self.region_key: str | None = None
        self.region: lore2.Region | None = None
        self.dungeon: dg.Dungeon | None = None
        self.monsters: list[ent.Monster] = []
        self.ground: list[dict] = []
        self.visible: set[tuple[int, int]] = set()
        self.selected = "vhaldor"
        self.turn = 0
        self.dead = False
        self.dead_cause = ""
        self.ending: str | None = None
        self.quit_run = False
        self.fragments = 1
        self.souvenirs = 0
        self.cleared: set[str] = set()
        self.knowledge = 0
        self.kael_ally = False
        self.aureth_deal = False
        self.final_boss: ent.Monster | None = None
        self.boss: ent.Monster | None = None
        self.last_hit_by = ""

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
            if self.mode == "world" and self.player is not None:
                self.draw(ui.paint(" " + prompt, ui.GOLD, bold=True))
            elif self.player is not None:
                self.draw(ui.paint(" " + prompt, ui.GOLD, bold=True))
            else:
                self.term.clear()
                self.term.draw(["", "  " + ui.paint(prompt, ui.GOLD, bold=True)])
            key = self.term.getkey().lower()
            if key in ("o", "y", "enter", "space", " "):
                return True
            if key in ("n", "q", "esc"):
                return False

    def legacy_screen(self) -> bool:
        key = self.mem.endings[-1] if self.mem.endings else "aucun"
        legacy = lore2.LEGACY.get(key, lore2.LEGACY["aucun"])
        body = [""]
        for line in legacy["text"]:
            body.append(ui.paint(line, ui.BONE))
        body.append("")
        bonus = legacy["bonus"]
        bits = []
        if bonus["max_hp"]:
            bits.append(f"+{bonus['max_hp']} PV max")
        if bonus["atk"]:
            bits.append(f"+{bonus['atk']} attaque")
        if bonus["souvenirs"]:
            bits.append(f"+{bonus['souvenirs']} souvenirs")
        body.append(ui.paint("Héritage : " + ", ".join(bits), ui.GOLD))
        body.append("")
        body.append(ui.paint(f"Âmes perdues au chapitre II : {self.mem.ch2['deaths']}", ui.PURPLE))
        body.append(ui.paint(f"Souvenirs en réserve : {self.mem.ch2['souvenirs']}", ui.CYAN))
        k = self.modal("CE QUE TU AS LAISSÉ DERRIÈRE TOI", body,
                       "[Entrée] continuer   ·   [Q] renoncer", ui.GOLD).lower()
        return not (k == "q" or k == "esc")

    def prologue(self) -> None:
        self.modal(lore2.TITLE, [""] + [ui.paint(l, ui.BONE) if l else "" for l in lore2.PROLOGUE]
                   + ["", ui.paint(lore2.SUBTITLE, ui.PURPLE)],
                   "[Entrée] se réveiller dans le cercle de runes", ui.MAGENTA, 74)
        self.modal("ELDRIA, LA DERNIÈRE PROPHÉTESSE",
                   [""] + [ui.paint(l, ui.BONE) if l else "" for l in lore2.ELDRIA_INTRO],
                   "[Entrée] prendre le Cœur d'Ébène", ui.CYAN, 74)

    # =================================================================
    #  PARTIE
    # =================================================================
    def new_run(self) -> None:
        class_key = self.mem.data.get("class", "gardien")
        if class_key not in ent.CLASS_DEFS:
            class_key = "gardien"
        p = ent.Player(self.mem, class_key=class_key)
        self.player = p
        p.level = 4
        p.max_hp = 42
        p.base_atk = 5
        legacy_key = self.mem.endings[-1] if self.mem.endings else "aucun"
        bonus = lore2.LEGACY.get(legacy_key, lore2.LEGACY["aucun"])["bonus"]
        p.max_hp += bonus["max_hp"]
        p.base_atk += bonus["atk"]
        p.hp = p.max_hp
        p.weapon = items.make_ch2_weapon(0)
        p.armor = items.make_ch2_armor(0)
        p.xp = 0

        ch2 = self.mem.ch2
        grants = ch2.setdefault("legacy_grants", [])
        if legacy_key not in grants:
            # le bonus de souvenirs n'est accordé qu'une fois par héritage
            grants.append(legacy_key)
            ch2["souvenirs"] = int(ch2.get("souvenirs", 0)) + bonus["souvenirs"]
        self.souvenirs = int(ch2.get("souvenirs", 0))
        self.knowledge = int(ch2.get("knowledge", 0))
        self.kael_ally = bool(ch2.get("kael_ally", False))
        self.aureth_deal = bool(ch2.get("aureth_deal", False))
        ch2["knowledge"] = self.knowledge
        ch2["kael_ally"] = self.kael_ally
        ch2["aureth_deal"] = self.aureth_deal
        self.mem.save()

        self.fragments = 1            # Cœur d'Ébène
        p.fragments = self.fragments
        self.cleared = set()
        self.mode = "world"
        self.region = None
        self.region_key = None
        self.dungeon = None
        self.monsters = []
        self.ground = []
        self.turn = 0
        self.dead = False
        self.dead_cause = ""
        self.ending = None
        self.quit_run = False
        self.selected = "vhaldor"
        self.messages = []
        self.fam_taunt = 0
        self.depth = 3
        self.load_familiar()
        self.log(lore2.TITLE, ui.GOLD)
        self.log("Le Cœur d'Ébène bat dans ta main. Il est tiède.", ui.PURPLE)
        self.log("Six fragments dorment dans six régions. Trouve-les.", ui.GREY)

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
        if self.mode == "world":
            self.handle_world(key, low)
        else:
            self.handle_region(key, low)

    # =================================================================
    #  CARTE DU MONDE
    # =================================================================
    def handle_world(self, key: str, low: str) -> None:
        if low in KEYMAP:
            self.world_move(*KEYMAP[low])
            return
        if low in ("1", "2", "3", "4", "5", "6"):
            idx = int(low) - 1
            if idx < len(lore2.REGIONS):
                self.selected = lore2.REGIONS[idx].key
            return
        if low in ("e", "enter", "space", " "):
            self.world_enter()
            return
        if low == "i":
            self.open_inventory()
            return
        if low == "o":
            self.journal()
            return
        if low == "?":
            self.show_help()
            return
        if low == "q":
            if self.ask("Quitter le Chapitre II ? (la progression persiste) (o/n)"):
                self.quit_run = True
            return

    def world_move(self, dx: int, dy: int) -> None:
        if self.selected == ORIGIN:
            cx, cy = ORIGIN_POS
        else:
            region = lore2.REGION_BY_KEY[self.selected]
            cx, cy = region.pos
        best, best_score = None, 0.25
        targets = [(r.key, r.pos) for r in lore2.REGIONS] + [(ORIGIN, ORIGIN_POS)]
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

    def world_enter(self) -> None:
        if self.selected == ORIGIN:
            if self.fragments >= 7:
                self.enter_origin()
            else:
                self.log(f"L'Origine est scellée. Fragments : {self.fragments}/7.", ui.MAGENTA)
                self.log("« Apporte-les tous », souffle une voix qui n'est pas la tienne.", ui.PURPLE)
            return
        self.enter_region(self.selected)

    # =================================================================
    #  ENTRÉE DANS UNE RÉGION
    # =================================================================
    def enter_region(self, key: str) -> None:
        region = lore2.REGION_BY_KEY[key]
        self.region = region
        self.region_key = key
        self.mode = "region"
        depth = lore2.REGIONS.index(region) + 1
        self.dungeon = dg.generate(depth, self.rng)
        self.monsters = []
        self.ground = []
        self.turn = 0
        px, py = self.dungeon.start
        self.player.x, self.player.y = px, py
        self.dungeon.set_tile(px, py, "<")
        self.dungeon.features.append(dg.Feature(px, py, "exit", {}))
        self.place_familiar(px, py)
        self.depth = depth
        self.boss = None

        avoid = {(px, py), self.dungeon.stairs}

        if key not in self.cleared:
            bdef = region.boss
            bx, by = self.dungeon.stairs
            boss = ent.Monster.from_def(bdef, self.rng, depth)
            boss.x, boss.y = bx, by
            boss.awake = True
            self.monsters.append(boss)
            self.boss = boss

            count = 5 + depth
            for _ in range(count):
                mx = my = -1
                for _ in range(80):
                    mx, my = self.dungeon.free_tile(self.rng, avoid)
                    if abs(mx - px) + abs(my - py) >= 6:
                        break
                avoid.add((mx, my))
                mon = ent.Monster.from_def(self.rng.choice(region.monsters), self.rng, depth)
                mon.x, mon.y = mx, my
                self.monsters.append(mon)

        # --- PNJ -----------------------------------------------------------
        npc_key = region.npc
        if npc_key and not (npc_key == "kael" and self.kael_ally):
            room = self.rng.choice(self.dungeon.rooms[1:])
            nx, ny = self.dungeon.free_tile(self.rng, avoid, [room])
            avoid.add((nx, ny))
            npc = lore2.NPCS[npc_key]
            self.dungeon.set_tile(nx, ny, npc["glyph"])
            self.dungeon.features.append(dg.Feature(nx, ny, "npc", {"key": npc_key}))
        elif npc_key == "kael" and self.kael_ally:
            self.log("Kael est déjà à tes côtés. Il ne t'attend pas ici.", ui.GOLD)

        # --- stèle ---------------------------------------------------------
        stele = self.rng.choice(region.steles)
        sx, sy = self.dungeon.free_tile(self.rng, avoid)
        avoid.add((sx, sy))
        self.dungeon.set_tile(sx, sy, dg.INSCRIPTION)
        self.dungeon.features.append(dg.Feature(sx, sy, "stele", {"text": stele}))

        # --- échos de tes morts --------------------------------------------
        self.spawn_death_echoes(avoid)

        self.update_fov()
        self.log(f"— {region.name} —", ui.GOLD)
        self.log(region.subtitle, ui.MIDGREY)
        self.log(self.rng.choice(region.ambient), ui.GREY)
        self.log("[<] revenir à la carte du monde.", ui.MIDGREY)
        if key in self.cleared:
            self.log("Région purgée. Les morts y errent encore, sans roi.", ui.CYAN)

    def spawn_death_echoes(self, avoid: set[tuple[int, int]]) -> None:
        ch2 = self.mem.ch2
        deaths = int(ch2.get("deaths", 0))
        px, py = self.player.x, self.player.y
        specs = []
        if deaths >= 1:
            specs.append(("Souffle errant", "s", 22, 8, ()))
        if deaths >= 3:
            specs.append(("Écho équipé de ton armure", "Z", 40, 12, ("undead",)))
        if deaths >= 5:
            specs.append(("TON REFLET", "Y", 70, 18, ("fast",)))
        for name, glyph, hp, atk, traits in specs:
            mx = my = -1
            for _ in range(80):
                mx, my = self.dungeon.free_tile(self.rng, avoid)
                if abs(mx - px) + abs(my - py) >= 7:
                    break
            avoid.add((mx, my))
            mon = ent.Monster(name, glyph, ui.PURPLE if name == "TON REFLET" else ui.MIDGREY,
                              hp, hp, atk, 25, frozenset(traits), False)
            mon.x, mon.y = mx, my
            if name != "Souffle errant":
                drops = self._gear_from_last_death()
                mon.drops = drops
            self.monsters.append(mon)

    def _gear_from_last_death(self) -> list:
        log = self.mem.ch2.get("death_log", [])
        if not log:
            return []
        record = log[-1]
        drops = []
        for name in (record.get("weapon"), record.get("armor")):
            if not name:
                continue
            for key, wname, glyph, color, power, desc in items.CH2_WEAPONS:
                if wname == name:
                    drops.append(items.Item(f"c2_{key}", wname, glyph, color, "weapon", power, desc))
            for key, aname, glyph, color, power, desc in items.CH2_ARMORS:
                if aname == name:
                    drops.append(items.Item(f"c2_{key}", aname, glyph, color, "armor", power, desc))
        return drops

    def enter_origin(self) -> None:
        self.region = None
        self.region_key = ORIGIN
        self.mode = "region"
        self.dungeon = dg.generate(7, self.rng)
        self.monsters = []
        self.ground = []
        self.turn = 0
        px, py = self.dungeon.start
        self.player.x, self.player.y = px, py
        self.dungeon.set_tile(px, py, "<")
        self.dungeon.features.append(dg.Feature(px, py, "exit", {}))
        bx, by = self.dungeon.stairs
        boss = ent.Monster.from_def(
            ent.MonsterDef("LE PREMIER SILENCE", "∅", ui.WHITE, 260, 22, 400, 7, 7,
                           ("drain", "poison"), True), self.rng, 7)
        boss.x, boss.y = bx, by
        boss.awake = True
        if self.kael_ally:
            boss.max_hp -= 40
            boss.hp = boss.max_hp
            self.log("Kael entre avec toi, épée haute. Il n'a pas peur.", ui.GOLD)
        if self.aureth_deal:
            boss.max_hp += 50
            boss.hp = boss.max_hp
            self.log("Aureth t'a menti : sa force nourrit le Silence.", ui.RED)
        self.monsters.append(boss)
        self.boss = boss
        self.final_boss = boss
        # le cœur de L'Origine apparaîtra à l'emplacement du boss
        self.update_fov()
        self.log("— LE CŒUR DE L'ORIGINE —", ui.MAGENTA)
        self.log("La machine est vivante. Des milliers de visages respirent.", ui.PURPLE)
        self.log("Le Premier Silence t'attend au centre.", ui.WHITE)

    def leave_region(self) -> None:
        if self.region_key == ORIGIN:
            self.log("L'Origine ne te laissera pas partir. Pas encore.", ui.MAGENTA)
            return
        self.mode = "world"
        self.region = None
        self.region_key = None
        self.monsters = []
        self.ground = []
        self.dungeon = None
        self.log("Tu reviens à la lisière du monde.", ui.MIDGREY)

    # =================================================================
    #  DÉPLACEMENT / COMBAT (région)
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
        self.visible = dg.compute_fov(self.dungeon, self.player.x, self.player.y, 8)

    def handle_region(self, key: str, low: str) -> None:
        if low in KEYMAP:
            self.move(*KEYMAP[low])
            return
        if low in ("e", "enter"):
            self.interact()
            return
        if low == "<":
            self.leave_region()
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
        if low == "q":
            if self.ask("Quitter le Chapitre II ? (la progression persiste) (o/n)"):
                self.quit_run = True
            return
        if low == "r":
            self.log("Tu reprends ton souffle.", ui.MIDGREY)
            self.end_turn()

    def move(self, dx: int, dy: int) -> None:
        if self.dead or self.ending or self.mode != "region" or self.dungeon is None:
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
            self.log("Rien à forcer ici.", ui.MIDGREY)
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
            if g["x"] == p.x and g["y"] == p.y:
                if g["item"].owner == "familiar":
                    self.log("Ce butin appartient à ton familier. Tu n'y touches pas.", ui.MIDGREY)
                    continue
                self.ground.remove(g)
                self.log(p.add_item(g["item"]), ui.BONE)

    def check_tile(self) -> None:
        feat = self.dungeon.feature_at(self.player.x, self.player.y)
        if feat and feat.kind == "exit":
            self.log("Une sortie de région. [<] pour revenir à la carte.", ui.GOLD)

    def player_attack(self, mon: ent.Monster) -> None:
        p = self.player
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
        self.log(f"{mon.name} s'effondre.", ui.RED)
        for note in p.gain_xp(mon.xp):
            self.log(note, ui.GREEN)
        for it in loot_manager.roll_loot(mon, "player", self.depth, self.rng, chance=0.35):
            self.ground.append({"x": mon.x, "y": mon.y, "item": it})
        if getattr(self, "special_kael", None) is mon:
            self.kael_ally = True
            self.mem.ch2["kael_ally"] = True
            self.souvenirs += 2
            self.mem.ch2["souvenirs"] = self.souvenirs
            self.mem.save()
            self.log("Kael s'agenouille, vaincu. « Alors... tu es vraiment revenu. »", ui.GOLD)
            self.log("Il te suivra jusqu'au Silence.", ui.CYAN)
            self.special_kael = None
        if not mon.boss:
            return

        # ----- boss de région ------------------------------------------
        if self.region_key == ORIGIN:
            self.log("LE PREMIER SILENCE se tait. Le cœur de L'Origine bat seul.", ui.WHITE)
            self.log("Des milliers de visages te regardent. [E] pour décider.", ui.MAGENTA)
            self.dungeon.set_tile(mon.x, mon.y, dg.SHRINE)
            self.dungeon.features.append(dg.Feature(mon.x, mon.y, "heart", {}))
            self.final_boss = mon
            return

        self.cleared.add(self.region_key or "")
        self.fragments += 1
        p.fragments = self.fragments
        self.souvenirs += 3
        self.knowledge = self.mem.add_ch2_knowledge(1)
        self.mem.add_ch2_souvenirs(3)
        self.log(f"Le fragment de {self.region.name} est à toi. "
                 f"({self.fragments}/7)", ui.YELLOW)
        self.log("+3 souvenirs. +1 savoir.", ui.CYAN)
        self.ground.append({"x": mon.x, "y": mon.y,
                            "item": items.make_ch2_weapon(min(3, len(self.cleared)))})
        self.log("Le boss laisse tomber une arme. Ramasse-la.", ui.GOLD)
        if self.fragments >= 7:
            self.log("Les sept fragments vibrent. L'Origine s'ouvre.", ui.MAGENTA)

    def monster_attack(self, mon: ent.Monster) -> None:
        p = self.player
        raw = self.rng.randint(max(1, mon.atk - 3), mon.atk + 1)
        dmg = max(1, raw - p.defense)
        p.hurt(dmg)
        self.last_hit_by = mon.name
        self.log(f"{mon.name} te frappe : {dmg} dégâts.", ui.RED)
        if "poison" in mon.traits and self.rng.random() < 0.3 and p.poison <= 0:
            p.poison = 6
            self.log("Le venin entre. Ta peau froide ne le sent même pas.", ui.GREEN)
        if "drain" in mon.traits and self.rng.random() < 0.25 and p.max_hp > 8:
            p.max_hp -= 1
            p.hp = min(p.hp, p.max_hp)
            self.log("Il te vole un souvenir.", ui.PURPLE)
        if p.hp <= 0:
            self.die(self.last_hit_by or mon.name)

    def die(self, cause: str) -> None:
        if self.dead:
            return
        p = self.player
        p.hp = 0
        self.dead = True
        self.dead_cause = cause
        self.mem.record_ch2_death(self.region_key or "seuil", cause, p)
        self.mem.add_ch2_souvenirs(-min(2, self.souvenirs))
        self.souvenirs = int(self.mem.ch2["souvenirs"])

    def end_turn(self) -> None:
        if self.dead:
            return
        p = self.player
        self.turn += 1
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
        for mon in list(self.monsters):
            if not mon.alive or mon.spared or self.dead:
                continue
            self.monster_turn(mon)
        if self.dead:
            return
        self.familiar_turn()
        if self.rng.random() < 0.05:
            self.whisper()

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
                if is_fam:
                    self.monster_attack_familiar(mon)
                else:
                    self.monster_attack(mon)
                continue
            dx = (tx > mon.x) - (tx < mon.x)
            dy = (ty > mon.y) - (ty < mon.y)
            options = [(dx, 0), (0, dy)] if abs(tx - mon.x) >= abs(ty - mon.y) else [(0, dy), (dx, 0)]
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

    def whisper(self) -> None:
        deaths = int(self.mem.ch2.get("deaths", 0))
        if deaths >= 10 and self.rng.random() < 0.5:
            self.log(self.rng.choice(lore2.AMBUSH_WHISPERS), ui.WHITE)
        else:
            self.log("[Un murmure d'âme]  « Tu n'es pas immortel. La mort ne sait pas quoi faire de toi. »",
                     ui.PURPLE)

    # =================================================================
    #  INTERACTIONS
    # =================================================================
    def interact(self) -> None:
        p = self.player
        feat = self.dungeon.feature_at(p.x, p.y)
        if feat is None:
            for dx, dy in DIRS[:4]:
                feat = self.dungeon.feature_at(p.x + dx, p.y + dy)
                if feat is not None:
                    break
        if feat is None:
            self.log("Rien à toucher ici.", ui.MIDGREY)
            return
        if feat.kind == "exit":
            self.leave_region()
        elif feat.kind == "stele":
            self.read_stele(feat)
        elif feat.kind == "npc":
            self.talk(feat.data.get("key"))
        elif feat.kind == "heart":
            self.ending_choice()

    def read_stele(self, feat) -> None:
        text = feat.data.get("text", "")
        new = self.mem.add_inscription(text)
        self.log("[Stèle]", ui.CYAN)
        self.log(f"« {text} »", ui.BONE)
        if new:
            self.knowledge = self.mem.add_ch2_knowledge(1)
            self.log(f"+1 savoir ({self.knowledge}/4).", ui.PURPLE)
        else:
            self.log("Tu connaissais déjà ces mots.", ui.MIDGREY)

    def talk(self, npc_key: str) -> None:
        if npc_key not in lore2.NPCS:
            return
        npc = lore2.NPCS[npc_key]
        first = self.mem.meet_npc(npc_key)
        deaths = int(self.mem.ch2.get("deaths", 0))
        body = [""] + [ui.paint(line, ui.BONE) for line in npc["lines"]]
        if deaths >= 2 and first:
            body.append("")
            body.append(ui.paint("« Tu es déjà venu. Plusieurs fois. Je le vois. »", ui.PURPLE))
        body.append("")
        if npc_key == "kael":
            if self.kael_ally:
                body.append(ui.paint("Kael te suit désormais. Il a cessé de haïr.", ui.GOLD))
                self.modal(npc["name"], body, "[Entrée] continuer", ui.GOLD)
                return
            body.append(ui.paint(f"[C] Combattre   [P] Payer 3 souvenirs pour parler "
                                 f"({self.souvenirs} en poche)   [F] Fuir", ui.GOLD))
            while True:
                key = self.modal(npc["name"], body, "[ESC] reculer", ui.GOLD).lower()
                if key in ("esc", "f"):
                    return
                if key == "c":
                    self.duel_kael()
                    return
                if key == "p":
                    if self.souvenirs >= 3:
                        self.souvenirs -= 3
                        self.mem.ch2["souvenirs"] = self.souvenirs
                        self.kael_ally = True
                        self.mem.ch2["kael_ally"] = True
                        self.mem.save()
                        self.log("Kael baisse son épée. « Alors montre-moi que tu peux réparer. »",
                                 ui.GOLD)
                        self.log("Kael combattra à tes côtés contre le Silence.", ui.CYAN)
                    else:
                        self.log("Pas assez de souvenirs. Kael ricane.", ui.MIDGREY)
                    return
            return
        if npc_key == "lyra":
            healed = self.player.heal(self.player.max_hp)
            self.knowledge = self.mem.add_ch2_knowledge(1)
            body.append(ui.paint("Elle pose sa main froide sur la tienne.", ui.CYAN))
            body.append(ui.paint(f"Tu récupères {healed} PV et +1 savoir ({self.knowledge}/4).",
                                 ui.GREEN))
            self.modal(npc["name"], body, "[Entrée] continuer", ui.CYAN)
            return
        if npc_key == "morvan":
            body.append(ui.paint(f"Prix : 3 souvenirs (tu en as {self.souvenirs}).", ui.GOLD))
            body.append(ui.paint("[A] Acheter potions et parchemin   [B] Acheter une arme (6)   [ESC] partir",
                                 ui.GOLD))
            while True:
                key = self.modal(npc["name"], body, "[ESC] partir", ui.GOLD).lower()
                if key == "a" and self.souvenirs >= 3:
                    self.souvenirs -= 3
                    self.mem.ch2["souvenirs"] = self.souvenirs
                    self.mem.save()
                    self.player.add_item(items.make_potion(self.rng))
                    self.player.add_item(items.make_scroll(self.rng))
                    self.log("Morvan empoche trois souvenirs et te tend deux objets.", ui.GOLD)
                    return
                if key == "b" and self.souvenirs >= 6:
                    self.souvenirs -= 6
                    self.mem.ch2["souvenirs"] = self.souvenirs
                    self.mem.save()
                    tier = min(3, len(self.cleared))
                    w = items.make_ch2_weapon(tier)
                    self.player.add_item(w)
                    self.player.weapon = w
                    self.log(f"Morvan te vend {w.name}. Il sourit trop.", ui.GOLD)
                    return
                if key in ("esc", "q"):
                    self.log("« Reviens quand tu auras des souvenirs à perdre. »", ui.MIDGREY)
                    return
            return
        if npc_key == "aureth":
            if self.aureth_deal:
                body.append(ui.paint("« Notre marché tient toujours. »", ui.YELLOW))
                self.modal(npc["name"], body, "[Entrée] continuer", ui.YELLOW)
                return
            body.append(ui.paint(f"[A] Accepter son pouvoir   [R] Refuser et apprendre "
                                 f"({self.knowledge}/4)", ui.YELLOW))
            while True:
                key = self.modal(npc["name"], body, "[ESC] reculer", ui.YELLOW).lower()
                if key in ("esc",):
                    return
                if key == "a":
                    self.aureth_deal = True
                    self.mem.ch2["aureth_deal"] = True
                    self.player.max_hp += 8
                    self.player.hp = self.player.max_hp
                    self.player.base_atk += 3
                    self.mem.save()
                    self.log("Aureth pose sa main sur ton front. Tu te sens plus fort. Trop fort.",
                             ui.YELLOW)
                    self.log("Quelque chose sourit derrière son visage.", ui.RED)
                    return
                if key == "r":
                    self.knowledge = self.mem.add_ch2_knowledge(1)
                    self.log("Aureth ricane et s'efface. Tu as vu ce qu'il cachait.", ui.CYAN)
                    self.log(f"+1 savoir ({self.knowledge}/4).", ui.PURPLE)
                    return
            return

    def duel_kael(self) -> None:
        kael = ent.Monster("KAEL, le chevalier sans mort", "K", ui.GOLD, 90, 90, 18, 80,
                           frozenset(), False)
        kael.awake = True
        kael.drops = [items.make_ch2_weapon(2)]
        placed = False
        for dx, dy in DIRS:
            nx, ny = self.player.x + dx, self.player.y + dy
            if self.dungeon.walkable(nx, ny) and not self.monster_at(nx, ny):
                kael.x, kael.y = nx, ny
                placed = True
                break
        if not placed:
            kael.x, kael.y = self.dungeon.free_tile(self.rng, {(self.player.x, self.player.y)})
        self.monsters.append(kael)
        self.special_kael = kael
        self.log("Kael lève son épée. Trois siècles de haine dans un seul geste.", ui.RED)

    # =================================================================
    #  INVENTAIRE / AIDE / JOURNAL
    # =================================================================
    def open_inventory(self) -> None:
        p = self.player
        while True:
            body = [ui.paint(f" Souvenirs : {self.souvenirs}   PV : {p.hp}/{p.max_hp}   "
                             f"Savoir : {self.knowledge}/4", ui.GOLD),
                    ui.paint(" " + "─" * 58, ui.DARKGREY)]
            if not p.inventory:
                body.append("  (sac vide)")
            for idx, it in enumerate(p.inventory):
                letter = chr(ord("a") + idx)
                tag = " [équipée]" if it is p.weapon else (" [portée]" if it is p.armor else "")
                body.append(f"  {ui.paint(letter, ui.CYAN)}) {ui.paint(it.glyph, it.color)} "
                            f"{it.label}{ui.paint(tag, ui.GREEN)}")
            body.append(ui.paint(" " + "─" * 58, ui.DARKGREY))
            body.append(ui.paint(f"  Arme : {(p.weapon.name if p.weapon else 'mains nues')}"
                                 f"   Armure : {(p.armor.name if p.armor else 'aucune')}", ui.BONE))
            body.append(ui.paint("  [a-n] examiner/équiper/boire   [ESC] fermer", ui.MIDGREY))
            key = self.modal("SAC", body, "[ESC] retour", ui.CYAN, 64).lower()
            if key in ("esc", "i", "q"):
                return
            if len(key) == 1 and "a" <= key <= "n":
                idx = ord(key) - ord("a")
                if 0 <= idx < len(p.inventory):
                    self.use_item(p.inventory[idx])

    def use_item(self, item) -> None:
        p = self.player
        if item.kind == "accessory":
            ok, msg = p.equipment.equip(item, p.inventory)
            self.log(msg, ui.GOLD if ok else ui.MIDGREY)
            return
        if item.kind == "material":
            self.log("Un matériau : il sert à améliorer l'équipement.", ui.MIDGREY)
            return
        if item.kind in ("weapon", "armor"):
            if item is (p.weapon if item.kind == "weapon" else p.armor):
                self.log("Tu l'utilises déjà.", ui.MIDGREY)
                return
            if item.kind == "weapon":
                p.weapon = item
                self.log(f"Tu équipes {item.name} (+{item.power} dégâts).", ui.GOLD)
            else:
                p.armor = item
                self.log(f"Tu enfiles {item.name} (+{item.power} défense).", ui.GOLD)
            return
        if item.kind == "potion":
            self.log(f"Tu bois {item.name}.", ui.BONE)
            if "soin" in item.key:
                self.log(f"+{p.heal(item.power)} PV.", ui.GREEN)
            elif "antidote" in item.key:
                p.poison = 0
                self.log("Le venin se dissout.", ui.GREEN)
            elif "vigueur" in item.key:
                p.max_hp += item.power
                p.hp += item.power
                self.log(f"+{item.power} PV max.", ui.GREEN)
            p.remove_item(item)
            return
        if item.kind == "scroll":
            self.log(f"Tu lis {item.name}.", ui.CYAN)
            if "teleport" in item.key:
                x, y = self.dungeon.free_tile(self.rng)
                p.x, p.y = x, y
                self.update_fov()
                self.log("Le monde se plie.", ui.CYAN)
            elif "carto" in item.key:
                for yy in range(self.dungeon.height):
                    for xx in range(self.dungeon.width):
                        if self.dungeon.tile(xx, yy) != dg.WALL:
                            self.dungeon.explored.add((xx, yy))
                self.log("La région s'imprime dans ton crâne.", ui.CYAN)
            elif "flammes" in item.key:
                hit = 0
                for mon in self.monsters:
                    if mon.alive and (mon.x, mon.y) in self.visible:
                        if mon.take_damage(item.power):
                            self.on_monster_death(mon)
                        hit += 1
                self.log(f"Le feu jaillit. {hit} créature(s) touchée(s).", ui.ORANGE)
            p.remove_item(item)
            self.end_turn()
            return
        if item.kind == "key":
            self.log("La clé du chapitre I. Elle ne sert plus à rien ici.", ui.PURPLE)
            return
        self.log("Tu ne peux rien en faire.", ui.MIDGREY)

    def journal(self) -> None:
        ch2 = self.mem.ch2
        body = ["", ui.paint(f"Âmes perdues : {ch2['deaths']}", ui.PURPLE),
                ui.paint(f"Souvenirs : {self.souvenirs}   Savoir : {self.knowledge}/4", ui.GOLD)]
        legacy = self.mem.endings[-1] if self.mem.endings else "aucun"
        body.append(ui.paint(f"Héritage du Chapitre I : {legacy}", ui.CYAN))
        body.append(ui.paint(" " + "─" * 58, ui.DARKGREY))
        body.append(ui.paint("RÉGIONS", ui.GOLD, bold=True))
        for r in lore2.REGIONS:
            mark = "✓ purgée" if r.key in self.cleared else "· intacte"
            body.append(f"  {r.short:<10} {mark}")
        body.append("")
        body.append(ui.paint("PNJ rencontrés : " + (", ".join(ch2["npcs"]) or "aucun"), ui.BONE))
        if ch2["endings"]:
            body.append(ui.paint("Fins du Chapitre II : " + ", ".join(ch2["endings"]), ui.GOLD))
        self.modal("JOURNAL", body, "[ESC] retour", ui.CYAN, 66)

    def show_help(self) -> None:
        if self.mode == "world":
            body = [
                ui.paint("CARTE DU MONDE", ui.GOLD, bold=True),
                "  Flèches / WASD — choisir une région",
                "  [1-6] — sélection directe   [E] ou [Entrée] — y entrer",
                "  L'Origine (Ω) s'ouvre avec les 7 fragments.",
                "",
                ui.paint("RÈGLES DU CHAPITRE II", ui.GOLD, bold=True),
                "  Chaque région abrite un boss et un fragment.",
                "  Les souvenirs se dépensent chez Morvan (3 ou 6).",
                "  Le savoir (stèles, Lyra, Aureth) débloque la Vérité Interdite (4).",
                "  La mort est définitive — mais elle change le monde.",
            ]
        else:
            body = [
                ui.paint("EXPLORATION", ui.GOLD, bold=True),
                "  WASD / flèches — se déplacer, attaquer en marchant",
                "  [E] — stèle, PNJ, cœur de L'Origine",
                "  [<] — revenir à la carte du monde",
                "  [I] sac   [P] compagnon   [O] journal   [R] attendre   [Q] quitter",
                "",
                ui.paint("MORT", ui.GOLD, bold=True),
                "  Chaque mort est enregistrée et modifie le monde :",
                "  1 âme perdue, 3 ennemis équipés de toi, 5 ton reflet, 10 le Silence.",
            ]
        self.modal("AIDE", body, "[ESC] retour", ui.GOLD, 72)

    # =================================================================
    #  FINS
    # =================================================================
    def ending_choice(self) -> None:
        p = self.player
        options = list(lore2.ENDING_CHOICES)
        locked = self.knowledge < 4
        while True:
            body = [ui.paint("Des milliers de visages te regardent depuis les parois.", ui.PURPLE), ""]
            for key, ending, label in options:
                if ending == "verite_interdite" and locked:
                    body.append(f"  {ui.paint('[' + key + ']', ui.DARKGREY)} "
                                f"{ui.paint(label + f'  (savoir {self.knowledge}/4)', ui.DARKGREY)}")
                else:
                    body.append(f"  {ui.paint('[' + key + ']', ui.GOLD)} {label}")
            body.append("")
            body.append(ui.paint(f"  Souvenirs : {self.souvenirs}   Savoir : {self.knowledge}/4"
                                 f"   Fragments : {self.fragments}/7", ui.MIDGREY))
            choice = self.modal("LE CŒUR DE L'ORIGINE", body,
                                "[ESC] reculer encore un peu", ui.MAGENTA, 72).lower()
            if choice == "esc":
                return
            for key, ending, _label in options:
                if choice == key:
                    if ending == "verite_interdite" and locked:
                        self.log("Tu ne sais pas encore assez. Le silence te repousse.", ui.RED)
                        continue
                    self.ending = ending
                    self.mem.record_ch2_ending(ending)
                    return

    def ending_screen(self, key: str) -> None:
        data = lore2.ENDINGS[key]
        body = [""] + [ui.paint(l, ui.BONE) if l else "" for l in data["lines"]]
        body += ["", ui.paint("─" * 58, ui.DARKGREY),
                 ui.paint(f"Fins du Chapitre II : {len(self.mem.ch2['endings'])}/5", ui.GOLD),
                 ui.paint(f"Âmes perdues : {self.mem.ch2['deaths']}", ui.PURPLE)]
        self.modal(str(data["title"]), body, "[Entrée] continuer", int(data["colour"]), 72)

    def final_scene(self) -> None:
        body = [""]
        for line in lore2.FINAL_SCENE:
            body.append(ui.paint(line, ui.GREY) if line else "")
        self.modal("FIN DU CHAPITRE II", body, "[Entrée] ...", ui.WHITE, 72)

        body = [""]
        for line in lore2.CREATOR_UNLOCK:
            colour = ui.GOLD if line.startswith("[") else ui.PURPLE
            body.append(ui.paint(line, colour))
        body += ["", ui.paint("La suite n'existe pas encore. Ou elle existe déjà.", ui.MIDGREY)]
        self.modal("SOUVENIR DÉBLOQUÉ", body, "[Entrée] revenir au seuil", ui.MAGENTA, 62)
        self.mem.ch2["ch3_teaser"] = True
        self.mem.save()

    def death_screen(self) -> bool:
        ch2 = self.mem.ch2
        deaths = int(ch2.get("deaths", 0))
        body = ["", ui.paint("Ton âme quitte ton corps. Elle ne va nulle part.", ui.PURPLE),
                ui.paint(f"Tu meurs dans {self.region.name if self.region else 'le vide'} — "
                         f"{self.dead_cause}.", ui.RED),
                "",
                f"Niveau {self.player.level}   ·   {self.player.kills} créatures tuées"
                f"   ·   Fragments {self.fragments}/7",
                ui.paint(f"Âmes perdues au total : {deaths}", ui.GOLD)]
        tier_text = lore2.DEATH_TIERS.get(deaths)
        if tier_text:
            body += ["", ui.paint("LE MONDE CHANGE :", ui.RED, bold=True),
                     ui.paint(tier_text, ui.PURPLE)]
        body += ["", ui.paint("Le monde se souviendra de cette mort.", ui.MIDGREY), ""]
        key = self.modal("MORT", body, "[Entrée] revenir dans le cercle de runes   ·   [Q] quitter",
                         ui.RED, 72).lower()
        return not (key == "q" or key == "esc")

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
        ch2 = self.mem.ch2
        lines = ["╔" + "═" * inner + "╗"]
        title = (f"CHAPITRE II · LE ROYAUME DES ÂMES BRISÉES  ·  Âmes {ch2['deaths']}"
                 f"  ·  Souvenirs {self.souvenirs}")
        lines.append("║" + ui.pad(ui.paint(title, ui.GOLD, bold=True), inner, "center") + "║")
        lines.append("╠" + "═" * inner + "╣")
        rows = self._world_rows() if self.mode == "world" else self._region_rows()
        for row in rows:
            lines.append("║" + row + "║")
        lines.append("╠" + "═" * inner + "╣")
        lines.append("║" + ui.pad(self._status_line(), inner) + "║")
        lines.append("╠" + "═" * inner + "╣")
        for row in self._log_rows():
            lines.append("║" + ui.pad(row, inner) + "║")
        lines.append("╠" + "═" * inner + "╣")
        if help_line is None:
            if self.mode == "world":
                help_line = ui.paint("[WASD] choisir  [E] entrer  [I] sac  [P] compagnon  "
                                     "[?] aide  [Q] quitter", ui.MIDGREY)
            else:
                help_line = ui.paint("[WASD] bouger  [E] interagir  [<] sortir  [I] sac  "
                                     "[O] journal  [?] aide", ui.MIDGREY)
        lines.append("║" + ui.pad(help_line, inner) + "║")
        lines.append("╚" + "═" * inner + "╝")
        return lines

    # --- monde ---------------------------------------------------------
    def _world_rows(self) -> list[str]:
        grid = [[" " for _ in range(self.MAP_W)] for _ in range(self.MAP_H)]
        colours = [[ui.DARKGREY for _ in range(self.MAP_W)] for _ in range(self.MAP_H)]

        def put(x: int, y: int, ch: str, colour: int) -> None:
            if 0 <= x < self.MAP_W and 0 <= y < self.MAP_H:
                grid[y][x] = ch
                colours[y][x] = colour

        ox, oy = ORIGIN_POS
        # chemins décoratifs
        for r in lore2.REGIONS:
            for x, y in list(dg._line(ox, oy, r.pos[0], r.pos[1]))[1:-1]:
                if grid[y][x] == " ":
                    put(x, y, "·", ui.VOID)
        # noeuds
        for r in lore2.REGIONS:
            x, y = r.pos
            if r.key == self.selected:
                ch, colour = "@", ui.WHITE
            elif r.key in self.cleared:
                ch, colour = "✓", ui.GREEN
            else:
                ch, colour = "◆", ui.BONE
            put(x, y, ch, colour)
            lx = x - len(r.short) - 2 if r.label_left else x + 2
            for i, c in enumerate(r.short):
                put(lx + i, y, c, ui.MIDGREY if r.key != self.selected else ui.GOLD)
            gap = range(lx + len(r.short), x) if r.label_left else range(x + 1, lx)
            for gx in gap:
                put(gx, y, " ", ui.VOID)
        # origine
        unlocked = self.fragments >= 7
        if self.selected == ORIGIN:
            put(ox, oy, "@", ui.WHITE)
        else:
            put(ox, oy, "Ω" if unlocked else "Ω", ui.MAGENTA if unlocked else ui.DARKGREY)
        put(ox + 1, oy, " ", ui.VOID)
        for i, c in enumerate("L'ORIGINE"):
            put(ox + 2 + i, oy, c, ui.MAGENTA if unlocked else ui.DARKGREY)

        # panneau
        rows = []
        for y in range(self.MAP_H):
            row = "".join(ui.paint(grid[y][x], colours[y][x]) for x in range(self.MAP_W))
            rows.append(row + "│" + self._panel_row(y))
        return rows

    # --- région --------------------------------------------------------
    def _region_rows(self) -> list[str]:
        ox, oy = self._viewport()
        rows = []
        for sy in range(oy, oy + self.MAP_H):
            cells = []
            for sx in range(ox, ox + self.MAP_W):
                cells.append(self._cell(sx, sy))
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
        fam_cell = self.familiar_cell(x, y, lit)
        if fam_cell is not None:
            return fam_cell
        tile = dng.tile(x, y)
        region = self.region
        ch, colour = " ", ui.VOID
        if tile == dg.WALL:
            ch = region.wall_glyph if region else "▓"
            colour = region.wall_color if region else ui.MIDGREY
        elif tile == dg.FLOOR:
            ch = region.floor_glyph if region else "·"
            colour = region.floor_color if region else ui.MIDGREY
        elif tile == "<":
            ch, colour = "<", ui.GOLD
        elif tile == dg.INSCRIPTION:
            ch, colour = "†", ui.CYAN
        elif tile == dg.SHRINE:
            ch, colour = "Φ", ui.MAGENTA
        elif tile == dg.STAIRS:
            ch, colour = "·", region.floor_color if region else ui.MIDGREY

        if lit:
            for g in self.ground:
                if (g["x"], g["y"]) == (x, y):
                    it = g["item"]
                    return ui.paint(it.glyph, it.color)
            for mon in self.monsters:
                if mon.alive and not mon.spared and (mon.x, mon.y) == (x, y):
                    return ui.paint(mon.glyph, ui.MAGENTA if mon.boss else mon.color,
                                    bold=mon.boss)
            feat = dng.feature_at(x, y)
            if feat and feat.kind == "npc":
                npc = lore2.NPCS.get(feat.data.get("key", ""))
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

    # --- panneau -------------------------------------------------------
    def _panel_row(self, i: int) -> str:
        p = self.player
        rule = ui.paint(" " + "─" * 28, ui.DARKGREY)
        if self.mode == "world":
            if self.selected == ORIGIN:
                name = "L'ORIGINE"
                subtitle = ["La machine vivante.", "Des milliers de visages."]
                boss = "LE PREMIER SILENCE"
                state = "ouverte" if self.fragments >= 7 else f"scellée ({self.fragments}/7)"
            else:
                region = lore2.REGION_BY_KEY[self.selected]
                name = region.short
                wrapped = ui.wrap(region.subtitle, 26)
                subtitle = wrapped[:2]
                if len(wrapped) > 2 and len(subtitle) > 1:
                    subtitle[1] = subtitle[1][:24].rstrip() + "…"
                boss = region.boss.name
                state = "purgée" if region.key in self.cleared else "intacte"
            rows = [
                ui.paint(f" {name}", ui.GOLD, bold=True),
                rule,
                f" {subtitle[0] if len(subtitle) > 0 else ''}",
                f" {subtitle[1] if len(subtitle) > 1 else ''}",
                "",
                rule,
                ui.paint(" BOSS", ui.MIDGREY),
                f" {boss}",
                f" État : {state}",
                rule,
                ui.paint(f" Fragments {self.fragments}/7", ui.YELLOW),
                ui.paint(f" Souvenirs {self.souvenirs}  Savoir {self.knowledge}/4", ui.CYAN),
                ui.paint(f" Âmes perdues {self.mem.ch2['deaths']}", ui.PURPLE),
                rule,
                ui.paint(" [E] entrer", ui.BONE),
                ui.paint(" [O] journal   [I] sac", ui.MIDGREY),
            ]
        else:
            weapon, armor = p.equipment_summary()
            rows = [
                ui.paint(f" {(self.region.short if self.region else 'ORIGINE')}", ui.GOLD, bold=True),
                rule,
                f" PV   {self._bar(p.hp, p.max_hp, 10)} {p.hp:>2}/{p.max_hp:<3}",
                f" Niv {p.level:<2} XP {p.xp:>2}/{p.xp_needed:<3}",
                ui.paint(f" Souvenirs {self.souvenirs}   Savoir {self.knowledge}/4", ui.CYAN),
                rule,
                f" Arme   {weapon}",
                f" Armure {armor}",
                rule,
            ]
            inv = p.inventory[:4]
            for idx, it in enumerate(inv):
                letter = chr(ord("a") + idx)
                rows.append(f" {ui.paint(letter, ui.MIDGREY)}) {it.label}")
            for _ in range(4 - len(inv)):
                rows.append("")
            rows += [
                rule,
                ui.paint(f" Fragments {self.fragments}/7", ui.YELLOW),
                ui.paint(f" Tour {self.turn}   {p.kills} tués", ui.MIDGREY),
            ]
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
        weapon, _ = p.equipment_summary()
        left = (f" PV {p.hp}/{p.max_hp}   Niv {p.level}   Arme: {weapon[:22]}   "
                f"Fragments {self.fragments}/7")
        if p.poison:
            left += ui.paint("   [POISON]", ui.GREEN)
        extra = self.familiar_status()
        if extra and ui.vlen(left) + len(extra) <= 76:
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
        if not self.legacy_screen():
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