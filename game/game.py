"""Boucle de jeu, rendu ASCII, combats, événements et fins."""
from __future__ import annotations

import random

from . import dungeon as dg
from . import entities as ent
from . import familiar_field, items, lore, loot_manager, ui


KEYMAP = {
    "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
    "k": (0, -1), "j": (0, 1), "h": (-1, 0), "l": (1, 0),
    "y": (-1, -1), "u": (1, -1), "b": (-1, 1), "n": (1, 1),
    "UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0),
}

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]


class Game(familiar_field.FamiliarField):
    MAP_W = 46
    MAP_H = 16
    PANEL_W = 30
    INNER = MAP_W + 1 + PANEL_W  # 77

    def __init__(self, term, memory, seed: int | None = None):
        self.term = term
        self.mem = memory
        self.seed = seed
        self.rng = random.Random(seed)
        self.messages: list[tuple[str, int]] = []
        self.player: ent.Player | None = None
        self.dungeon: dg.Dungeon | None = None
        self.depth = 1
        self.monsters: list[ent.Monster] = []
        self.ground: list[dict] = []
        self.visible: set[tuple[int, int]] = set()
        self.turn = 0
        self.dead = False
        self.dead_cause = ""
        self.ending: str | None = None
        self.quit_run = False
        self.quests: dict[str, bool] = {}
        self.stats = {"secrets": 0}
        self._class_key = "gardien"  # classe sélectionnée

    # =================================================================
    #  ÉCRANS GÉNÉRAUX
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
            # une ligne déjà colorée ne doit pas être re-découpée sur ses échappements
            chunks = [row] if "\x1b" in row else ui.wrap(row, inner - 2)
            for chunk in chunks:
                lines.append("║ " + ui.pad(chunk, inner - 2) + " ║")
        lines.append("╠" + "═" * inner + "╣")
        lines.append("║ " + ui.pad(ui.paint(footer, ui.GREY), inner - 2) + " ║")
        lines.append("╚" + "═" * inner + "╝")
        self.term.clear()
        self.term.draw([""] + lines)
        return self.term.getkey()

    def title_screen(self) -> bool:
        """Retourne False si le joueur quitte."""
        while True:
            deaths = len(self.mem.deaths)
            body = [""]
            for line in lore.INTRO:
                body.append(ui.paint(line, ui.BONE) if line else "")
            body.append("")
            body.append(ui.paint("─" * 60, ui.DARKGREY))
            body.append(ui.paint(
                f"Cycle {self.mem.cycle}   ·   Morts enregistrées : {deaths}   ·   "
                f"Intuition : {self.mem.insight}", ui.PURPLE))
            body.append(ui.paint(f"Profondeur record : {self.mem.best_depth}/7   ·   "
                                 f"Fins découvertes : {len(self.mem.endings)}/5", ui.MIDGREY))
            if deaths:
                last = self.mem.last_death() or {}
                body.append(ui.paint(
                    f"Dernière mort : étage {last.get('floor')} — {last.get('cause')}", ui.RED))
            body.append("")
            body.append(ui.paint("[Entrée] Entrer   [R] Effacer la mémoire   [Q] Quitter", ui.GREY))
            key = self.modal(lore.TITLE, body, "Le donjon se souvient de toi.", ui.GOLD)
            key = key.lower()
            if key == "q" or key == "esc":
                return False
            if key == "r":
                if self.ask_confirm("Effacer toute la mémoire du donjon ? (o/n)"):
                    self.mem.reset()
                continue
            if key in ("enter", "space", "\r", " "):
                # Sélection de classe au premier cycle
                if self.mem.cycle == 1:
                    class_key = self._select_class()
                    self.mem.data["class"] = class_key
                    self.mem.save()
                else:
                    class_key = self.mem.data.get("class", "gardien")
                self._class_key = class_key
                return True
            continue

    def _select_class(self) -> str:
        """Écran de sélection de classe."""
        body = [
            ui.paint("CHOISIS TON VISAGE", ui.GOLD, bold=True),
            "",
            ui.paint("[G]ardien", ui.GREEN, bold=True),
            "  +4 PV max · Armure de cuir · Attaque +1",
            "",
            ui.paint("[R]ôdeur", ui.GREEN, bold=True),
            "  +1 intuition immédiate · Dégâts +1",
            "",
            ui.paint("[S]orcier", ui.GREEN, bold=True),
            "  -2 PV max · Parchemin de flammes · Insight +1",
            "",
            ui.paint("─" * 40, ui.DARKGREY),
            "Le choix est gravé dans la cendre. Il te suivra.",
        ]
        while True:
            key = self.modal("NOUVEL AVENTURIER", body, "[ESC] retour", ui.GOLD, 50).lower()
            if key == "g":
                return "gardien"
            if key == "r":
                return "rodeur"
            if key == "s":
                return "sorcier"
            if key == "esc":
                return "gardien"  # fallback

    def ask_confirm(self, prompt: str) -> bool:
        while True:
            if self.player is None:
                # écran de titre : pas encore de donjon à afficher
                self.term.clear()
                self.term.draw(["", "  " + ui.paint(prompt, ui.GOLD, bold=True)])
            else:
                self.draw(ui.paint(" " + prompt, ui.GOLD, bold=True))
            k = self.term.getkey().lower()
            if k in ("o", "y", "enter", "space", " "):
                return True
            if k in ("n", "q", "esc"):
                return False

    # =================================================================
    #  PARTIE
    # =================================================================
    def new_run(self) -> None:
        class_key = getattr(self, '_class_key', 'gardien')
        self.player = ent.Player(self.mem, class_key=class_key)
        # Bonus insight pour rôdeur/sorcier au premier cycle
        if class_key in ("rodeur", "sorcier") and self.mem.cycle == 1:
            self.player.insight += 1
            self.mem.data["insight"] = min(9, self.mem.data.get("insight", 0) + 1)
        # Compétence Mémoriale : +1 PV max par cycle après le 2e
        if "cycle_hp_bonus" in self.player.unlocked_skills and self.mem.cycle > 2:
            bonus = (self.mem.cycle - 2)
            self.player.max_hp += bonus
            self.player.hp = min(self.player.hp + bonus, self.player.max_hp)
        self.depth = 1
        self.turn = 0
        self.dead = False
        self.dead_cause = ""
        self.ending = None
        self.quit_run = False
        self.quests = {}
        self.messages = []
        self.familiar = None
        self.fam_taunt = 0
        self.load_familiar()
        self.log(lore.TITLE, ui.GOLD)
        self.log("[Une inscription sur le mur]", ui.PURPLE)
        for line in lore.WALL_MESSAGE:
            self.log(line.strip(), ui.PURPLE)
        if self.mem.cycle > 1:
            self.log(f"Cycle {self.mem.cycle}. Tu es déjà mort {len(self.mem.deaths)} fois.", ui.RED)
            if self.mem.insight:
                self.log(f"Tu conserves {self.mem.insight} fragment(s) de mémoire.", ui.CYAN)
        self.load_floor(1)

    def load_floor(self, depth: int) -> None:
        self.depth = depth
        theme = lore.THEMES[depth]
        self.dungeon = dg.generate(depth, self.rng)
        self.monsters = []
        self.ground = []
        self.turn = 0
        px, py = self.dungeon.start
        self.player.x, self.player.y = px, py
        self.place_familiar(px, py)

        # --- boss / trône ---------------------------------------------------
        self.boss = None
        if depth in ent.BOSSES:
            bdef = ent.BOSSES[depth]
            bx, by = self.dungeon.stairs
            if depth == 7:
                # le trône remplace l'escalier
                self.dungeon.set_tile(bx, by, dg.THRONE)
                self.dungeon.stairs = (bx, by)
                self.dungeon.features.append(
                    dg.Feature(bx, by, "throne", {"used": False}))
                bx, by = bx - 2 if self.dungeon.tile(bx - 2, by) == dg.FLOOR else bx + 2, by
                if self.dungeon.tile(bx, by) != dg.FLOOR:
                    bx, by = self.dungeon.free_tile(self.rng, {(px, py)})
            boss = ent.Monster.from_def(bdef, self.rng, depth)
            boss.x, boss.y = bx, by
            boss.awake = True
            self.monsters.append(boss)
            self.boss = boss
        else:
            self.boss = None

        # --- monstres -------------------------------------------------------
        avoid = {(px, py), self.dungeon.stairs}
        count = 4 + depth + self.rng.randint(0, 2)
        pool = [m for m in ent.MONSTER_TABLE if m.depth_min <= depth <= m.depth_max]
        for _ in range(count):
            # jamais de monstre collé au point de départ
            mx = my = -1
            for _attempt in range(80):
                mx, my = self.dungeon.free_tile(self.rng, avoid)
                if abs(mx - px) + abs(my - py) >= 6:
                    break
            avoid.add((mx, my))
            mdef = self.rng.choice(pool)
            mon = ent.Monster.from_def(mdef, self.rng, depth)
            mon.x, mon.y = mx, my
            self.monsters.append(mon)

        # --- le squelette de ton ancien toi ---------------------------------
        record = self.mem.death_on_floor(depth)
        if record:
            mx, my = self.dungeon.free_tile(self.rng, avoid)
            avoid.add((mx, my))
            hp = 16 + depth * 3
            sk = ent.Monster(f"Squelette du cycle {record.get('cycle')}", "Z", ui.BONE,
                             hp, hp, 5 + depth, 10 + depth * 2,
                             frozenset({"undead"}), False)
            sk.x, sk.y = mx, my
            sk.drops = self._gear_from_record(record)
            # Rarement, le squelette drop un cœur de quest
            if self.rng.random() < 0.15:
                sk.drops.append(items.make_quest_heart())
            self.monsters.append(sk)
            self.log("Un squelette porte ton ancienne armure. Il se tourne vers toi.", ui.RED)

        # --- objets au sol ---------------------------------------------------
        for _ in range(2 + self.rng.randint(0, 2)):
            gx, gy = self.dungeon.free_tile(self.rng, avoid)
            avoid.add((gx, gy))
            self.ground.append({"x": gx, "y": gy, "item": items.make_loot(depth, self.rng)})

        # --- inscriptions -----------------------------------------------------
        texts = list(lore.INSCRIPTIONS.get(depth, []))
        self.rng.shuffle(texts)
        unread = [t for t in texts if not self.mem.has_read(t)]
        order = unread + [t for t in texts if self.mem.has_read(t)]
        idx = 0
        for feat in self.dungeon.features:
            if feat.kind == "inscription":
                feat.data["text"] = order[idx % len(order)]
                idx += 1

        self.update_fov()
        self.log(f"— {theme.name} —", ui.GOLD)
        self.log(theme.subtitle, ui.MIDGREY)
        self.log(self.rng.choice(theme.ambient), ui.GREY)
        if depth == 7:
            self.log("Le trône du Néant t'attend. Il n'y a plus de descente.", ui.MAGENTA)
        elif depth == 1 and self.mem.cycle == 1:
            self.log("Tu tiens une vieille clé noire. Tu ne sais pas pourquoi.", ui.GREY)

    def _gear_from_record(self, record: dict) -> list:
        drops = []
        for name in (record.get("weapon"), record.get("armor")):
            if not name:
                continue
            for key, wname, glyph, color, power, desc in items.WEAPONS:
                if wname == name:
                    drops.append(items.Item(f"w_{key}", wname, glyph, color, "weapon", power, desc))
            for key, aname, glyph, color, power, desc in items.ARMORS:
                if aname == name:
                    drops.append(items.Item(f"a_{key}", aname, glyph, color, "armor", power, desc))
        return drops

    # =================================================================
    #  LOG
    # =================================================================
    def log(self, text: str, colour: int = ui.GREY) -> None:
        self.messages.append((text, colour))
        if len(self.messages) > 120:
            self.messages = self.messages[-120:]

    @property
    def recent(self) -> list[tuple[str, int]]:
        return self.messages[-3:]

    # =================================================================
    #  RENDU
    # =================================================================
    def draw(self, help_line: str | None = None) -> None:
        self.term.draw(self.frame(help_line))

    def frame(self, help_line: str | None = None) -> list[str]:
        inner = self.INNER
        lines = ["╔" + "═" * inner + "╗"]
        title = (f"{lore.TITLE}  ·  Cycle {self.mem.cycle}"
                 f"  ·  Étage {self.depth}/7")
        lines.append("║" + ui.pad(ui.paint(title, ui.GOLD, bold=True), inner, "center") + "║")
        lines.append("╠" + "═" * inner + "╣")
        for row in self._map_rows():
            lines.append("║" + row + "║")
        lines.append("╠" + "═" * inner + "╣")
        lines.append("║" + ui.pad(self._status_line(), inner) + "║")
        lines.append("╠" + "═" * inner + "╣")
        loglines = self._log_rows()
        for row in loglines:
            lines.append("║" + ui.pad(row, inner) + "║")
        lines.append("╠" + "═" * inner + "╣")
        if help_line is None:
            help_line = ui.paint(
                "[WASD] bouger  [E] interagir  [I] sac  [P] compagnon  "
                "[>] descendre  [?] aide", ui.MIDGREY)
        lines.append("║" + ui.pad(help_line, inner) + "║")
        lines.append("╚" + "═" * inner + "╝")
        return lines

    def _map_rows(self) -> list[str]:
        ox, oy = self._viewport()
        theme = lore.THEMES[self.depth]
        rows = []
        for sy in range(oy, oy + self.MAP_H):
            cells = []
            for sx in range(ox, ox + self.MAP_W):
                cells.append(self._cell(sx, sy, theme))
            row = "".join(cells)
            rows.append(row + "│" + self._panel_row(sy - oy))
        return rows

    def _cell(self, x: int, y: int, theme) -> str:
        """Renvoie une seule cellule déjà colorée (1 caractère visible)."""
        dng = self.dungeon
        seen = (x, y) in dng.explored
        lit = (x, y) in self.visible
        if not seen:
            return " "

        # le joueur est toujours dessiné
        if self.player and (self.player.x, self.player.y) == (x, y):
            return ui.paint("@", ui.WHITE, bold=True)
        fam_cell = self.familiar_cell(x, y, lit)
        if fam_cell is not None:
            return fam_cell

        tile = dng.tile(x, y)
        ch, colour = " ", ui.VOID
        if tile == dg.WALL:
            ch, colour = "▓", theme.wall_color
        elif tile == dg.FLOOR:
            ch, colour = "·", theme.floor_color
        elif tile == dg.STAIRS:
            ch, colour = ">", ui.GOLD
        elif tile == dg.CHEST:
            ch, colour = "C", ui.GOLD
        elif tile == dg.INSCRIPTION:
            ch, colour = "†", ui.CYAN
        elif tile == dg.SHRINE:
            ch, colour = "Φ", ui.GREEN
        elif tile == dg.THRONE:
            ch, colour = "T", ui.MAGENTA
        elif tile == dg.WATER:
            ch, colour = "~", ui.BLUE

        if lit:
            for g in self.ground:
                if g["x"] == x and g["y"] == y:
                    it = g["item"]
                    return ui.paint(it.glyph, it.color)
            for mon in self.monsters:
                if mon.alive and not mon.spared and (mon.x, mon.y) == (x, y):
                    colour = ui.MAGENTA if mon.boss else mon.color
                    return ui.paint(mon.glyph, colour, bold=mon.boss)
            return ui.paint(ch, colour)

        # décor mémorisé (jamais les monstres ni le butin)
        dim_map = {
            ui.GOLD: ui.BROWN,
            ui.CYAN: ui.DARKGREY,
            ui.GREEN: ui.DARKGREEN,
            ui.MAGENTA: ui.PURPLE,
            ui.BLUE: ui.BLUE,
        }
        return ui.paint(ch, dim_map.get(colour, colour), dim=True)

    def _viewport(self) -> tuple[int, int]:
        dng = self.dungeon
        px, py = self.player.x, self.player.y
        ox = max(0, min(dng.width - self.MAP_W, px - self.MAP_W // 2))
        oy = max(0, min(dng.height - self.MAP_H, py - self.MAP_H // 2))
        return ox, oy

    def _panel_row(self, i: int) -> str:
        p = self.player
        theme = lore.THEMES[self.depth]
        weapon, armor = p.equipment_summary()
        rule = ui.paint(" " + "─" * 28, ui.DARKGREY)
        frag_dots = "".join("●" if i < p.fragments else "○" for i in range(7))
        rows: list[str] = [
            ui.paint(f" {theme.name}", ui.GOLD, bold=True),
            f" PV   {self._bar(p.hp, p.max_hp, 10)} {p.hp:>2}/{p.max_hp:<3}",
            f" Niv {p.level:<2} XP {p.xp:>2}/{p.xp_needed:<3} OR {p.gold:<4}",
            f" Intuition {p.insight}/9    Prof. {self.depth}/7",
            rule,
            f" Arme   {weapon}",
            f" Armure {armor}",
            ui.paint(" SAC [I] ", ui.CYAN) + ui.paint("─" * 20, ui.DARKGREY),
        ]
        inv = p.inventory[:5]
        for idx, it in enumerate(inv):
            letter = chr(ord("a") + idx)
            rows.append(f" {ui.paint(letter, ui.MIDGREY)}) {it.label}")
        for _ in range(5 - len(inv)):
            rows.append("")
        rows.append(rule)
        rows.append(ui.paint(f" Fragments {frag_dots} {p.fragments}/7", ui.YELLOW))
        rows.append(ui.paint(f" Tour {self.turn}    {p.kills} tués", ui.MIDGREY))
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
        weapon, armor = p.equipment_summary()
        left = (f" PV {p.hp}/{p.max_hp}   Niv {p.level}   Or {p.gold}   "
                f"Arme: {weapon[:20]}   Fragments {p.fragments}/7")
        if p.poison:
            left += ui.paint("   [POISON]", ui.GREEN)
        extra = self.familiar_status()
        if extra and ui.vlen(left) + len(extra) <= 76:
            left += ui.paint(extra, ui.CYAN)
        return ui.paint(" " + left, ui.BONE)

    def _log_rows(self) -> list[str]:
        rows = []
        for text, colour in self.recent:
            rows.append(" " + ui.paint(ui.truncate_colored(text, self.INNER - 3), colour))
        while len(rows) < 3:
            rows.append("")
        return rows[:3]

    # =================================================================
    #  BOUCLE
    # =================================================================
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
        if low in KEYMAP:
            self.move(*KEYMAP[low])
            return
        if low in (">", "enter"):
            self.try_descend()
            return
        if low == "e":
            self.interact()
            return
        if low == "i":
            self.open_inventory()
            return
        if low == "p":
            self.companion_menu()
            return
        if low == "g":
            self.pickup()
            return
        if low == "?":
            self.show_help()
            return
        if low == "q":
            if self.ask_confirm("Quitter la partie en cours ? (le cycle reste en cours) (o/n)"):
                self.quit_run = True
            return
        if low == "r":
            self.wait_turn()
            return

    def wait_turn(self) -> None:
        self.log("Tu reprends ton souffle.", ui.MIDGREY)
        self.end_turn()

    # =================================================================
    #  DÉPLACEMENT / COMBAT
    # =================================================================
    def monster_at(self, x: int, y: int) -> ent.Monster | None:
        for m in self.monsters:
            if m.alive and not m.spared and (m.x, m.y) == (x, y):
                return m
        return None

    def move(self, dx: int, dy: int) -> None:
        if self.dead or self.ending:
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
            self.log("Un mur. La crypte ne s'ouvre pas ici.", ui.MIDGREY)
            return
        p.x, p.y = nx, ny
        self.auto_pickup()
        self.update_fov()
        self.check_tile()
        if not self.dead:
            self.end_turn()

    def update_fov(self) -> None:
        self.visible = dg.compute_fov(self.dungeon, self.player.x, self.player.y, 8)

    def auto_pickup(self) -> None:
        p = self.player
        for g in list(self.ground):
            if g["x"] == p.x and g["y"] == p.y:
                if g["item"].owner == "familiar":
                    self.log("Ce butin appartient à ton familier. Tu n'y touches pas.", ui.MIDGREY)
                    continue
                self.ground.remove(g)
                msg = p.add_item(g["item"])
                self.log(f"Tu ramasses : {g['item'].name}. " + (
                    f"({p.fragments}/7)" if g["item"].kind == "fragment" else ""), ui.BONE)
                if g["item"].kind == "gold":
                    self.log(f"+{g['item'].power} pièces d'or.", ui.GOLD)
                if g["item"].kind == "fragment":
                    self.log("Un fragment divin pulse dans ta main.", ui.YELLOW)
                self.check_fragment_bonus()

    def check_fragment_bonus(self) -> None:
        p = self.player
        self.mem.data["fragments_max"] = max(int(self.mem.data.get("fragments_max", 0)), p.fragments)

    def check_tile(self) -> None:
        t = self.dungeon.tile(self.player.x, self.player.y)
        if t == dg.STAIRS:
            self.log("Un escalier descend. [Entrée] ou [>] pour descendre.", ui.GOLD)
        elif t == dg.THRONE:
            self.log("Le trône du Néant. [E] pour t'en approcher.", ui.MAGENTA)

    def player_attack(self, mon: ent.Monster) -> None:
        p = self.player
        dmg = p.damage_roll(self.rng)
        killed = mon.take_damage(dmg)
        weapon = p.weapon.name if p.weapon else "tes poings"
        self.log(f"Tu frappes {mon.name} avec {weapon} : {dmg} dégâts.", ui.WHITE)
        if killed:
            self.on_monster_death(mon)
            return
        # Un ennemi peut supplier d'être épargné
        if mon.hp <= max(2, mon.max_hp // 4) and not mon.boss and self.rng.random() < 0.18:
            if self.ask_confirm(f"{mon.name} gémit : « Pitié... je me souviens de toi. » L'épargner ? (o/n)"):
                mon.spared = True
                mon.awake = False
                self.log(f"Tu épargnes {mon.name}. Il recule dans l'ombre.", ui.CYAN)
                p.insight = min(9, p.insight + 1)
                if self.mem.add_inscription("« Tu as épargné l'un des tiens. »"):
                    self.log("Quelque chose s'éclaircit dans ta mémoire.", ui.PURPLE)
                    return

    def on_monster_death(self, mon: ent.Monster, killer: str = "player") -> None:
        if killer == "familiar":
            self.on_familiar_kill(mon)
            return
        p = self.player
        p.kills += 1
        self.log(f"{mon.name} s'effondre.", ui.RED)
        for note in p.gain_xp(mon.xp):
            self.log(note, ui.GREEN)
        drops = loot_manager.roll_loot(mon, "player", self.depth, self.rng, chance=0.4)
        if mon.boss:
            self.log("Le silence qui suit est plus lourd que le combat.", ui.MAGENTA)
            if self.depth == 7:
                self.log("Le trône est libre. [E] pour y monter.", ui.YELLOW)
                drops.append(items.make_weapon(7, self.rng))
            else:
                drops.append(items.make_weapon(self.depth + 1, self.rng))
                drops.append(items.make_armor(self.depth + 1, self.rng))
                self.log("Il laisse tomber une relique.", ui.GOLD)
        if self.familiar is not None and mon.boss:
            for it in loot_manager.boss_loot("familiar", self.depth, self.rng,
                                             self.familiar.class_key):
                self.ground.append({"x": mon.x, "y": mon.y, "item": it})
            self.log("Une part de butin revient à ton familier — la sienne.", ui.CYAN)
        for it in drops:
            it.owner = "player"
            self.ground.append({"x": mon.x, "y": mon.y, "item": it})
        if drops:
            self.log("Quelque chose brille parmi les restes.", ui.GREY)

    def monster_attack(self, mon: ent.Monster) -> None:
        p = self.player
        # Compétence Se Souvenir : les squelettes attaquent moins fort
        atk = mon.atk
        if "skeleton_weaken" in p.unlocked_skills and mon.name.startswith("Squelette"):
            atk = max(1, int(atk * 0.9))
        raw = self.rng.randint(max(1, atk - 3), atk + 1)
        dmg = max(1, raw - p.defense)
        p.hurt(dmg)
        self.log(f"{mon.name} te frappe : {dmg} dégâts.", ui.RED)
        self.last_hit_by = mon.name
        if "poison" in mon.traits and self.rng.random() < 0.35 and p.poison <= 0:
            p.poison = 6
            self.log("Le venin brûle dans tes veines.", ui.GREEN)
        if "drain" in mon.traits and self.rng.random() < 0.25:
            if p.max_hp > 6:
                p.max_hp -= 1
                p.hp = min(p.hp, p.max_hp)
                self.log("Il te vole un peu de ton souffle.", ui.PURPLE)
        if p.hp <= 0:
            self.die(self.last_hit_by if hasattr(self, "last_hit_by") else mon.name)

    def die(self, cause: str) -> None:
        if self.dead:
            return
        # Vérifier la compétence Dernier Souffle
        p = self.player
        if "last_breath" in p.unlocked_skills and not p.has_last_breath:
            self.log("Ton corps refuse de mourir. Les cendres te rendent à toi-même.", ui.YELLOW)
            p.hp = 5
            p.has_last_breath = True
            self.log("Dernier Souffle activé. Tu ne ressusciteras plus cette fois-ci.", ui.MIDGREY)
            return
        p.hp = 0
        self.dead = True
        self.dead_cause = cause
        self.mem.record_death(self.depth, cause, p)

    # =================================================================
    #  TOUR DES MONSTRES
    # =================================================================
    def end_turn(self) -> None:
        if self.dead:
            return
        p = self.player
        self.turn += 1

        # poison
        if p.poison > 0:
            p.poison -= 1
            if p.poison % 2 == 0:
                p.hurt(1)
                self.log("Le poison te ronge. (-1 PV)", ui.GREEN)
                if p.hp <= 0:
                    self.die("Empoisonnement")
                    return
        # régénération lente
        if self.turn % 12 == 0 and p.hp < p.max_hp and p.poison == 0:
            p.heal(1)

        # Compétence Écho Vivant : aperçu des chasseurs avant qu'ils ne bougent
        if "enemy_preview" in p.unlocked_skills:
            hunters = [m for m in self.monsters
                       if m.alive and not m.spared and m.awake and
                       (m.x, m.y) in self.visible]
            if hunters:
                nearest = min(hunters, key=lambda m: abs(m.x - p.x) + abs(m.y - p.y))
                d = abs(nearest.x - p.x) + abs(nearest.y - p.y)
                self.log(f"[Écho] {len(hunters)} menaçe(nt) · le plus proche : "
                         f"{nearest.name} à {d} case(s).", ui.CYAN)

        for mon in list(self.monsters):
            if not mon.alive or mon.spared or self.dead:
                continue
            self.monster_turn(mon)

        if self.dead:
            return

        self.familiar_turn()

        # murmures et événements
        if self.rng.random() < 0.055:
            self.random_event()
        elif self.rng.random() < 0.05:
            self.log(self.rng.choice(lore.WHISPERS), ui.PURPLE)

    def has_los(self, ax: int, ay: int, bx: int, by: int) -> bool:
        fifteen = list(dg._line(ax, ay, bx, by))
        for x, y in fifteen[1:-1]:
            if self.dungeon.tile(x, y) == dg.WALL:
                return False
        return True

    def monster_turn(self, mon: ent.Monster) -> None:
        p = self.player
        tx, ty, is_fam = self._target_of(mon)
        dist = abs(mon.x - tx) + abs(mon.y - ty)
        if not mon.awake:
            if dist <= 9 and self.has_los(mon.x, mon.y, p.x, p.y):
                mon.awake = True
            elif self.rng.random() < 0.30:
                self._step_random(mon)
                return
            else:
                return

        steps = 1
        if "fast" in mon.traits:
            steps = 2
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
            options = []
            if abs(tx - mon.x) >= abs(ty - mon.y):
                options = [(dx, 0), (0, dy)]
            else:
                options = [(0, dy), (dx, 0)]
            options += [d for d in DIRS if d not in options]
            moved = False
            for ddx, ddy in options:
                nx, ny = mon.x + ddx, mon.y + ddy
                if not self.dungeon.walkable(nx, ny):
                    continue
                if self.monster_at(nx, ny) or (nx, ny) == (tx, ty):
                    continue
                if (nx, ny) == self.dungeon.stairs and self.depth == 7:
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
    #  INTERACTIONS
    # =================================================================
    def try_descend(self) -> None:
        p = self.player
        if self.dungeon.tile(p.x, p.y) == dg.THRONE:
            self.throne_attempt()
            return
        if self.dungeon.tile(p.x, p.y) != dg.STAIRS:
            self.log("Il n'y a pas d'escalier ici.", ui.MIDGREY)
            return
        if self.depth >= 7:
            self.log("Le Néant n'a pas de fond.", ui.MAGENTA)
            return
        if self.monsters and any(m.alive and not m.spared and
                                 abs(m.x - p.x) + abs(m.y - p.y) <= 1
                                 for m in self.monsters):
            self.log("Impossible de descendre : quelque chose te retient.", ui.RED)
            return
        self.descend()

    def descend(self) -> None:
        self.depth += 1
        self.mem.data["best_depth"] = max(self.mem.best_depth, self.depth)
        self.mem.save()
        self.load_floor(self.depth)
        self.log("[Le donjon change. Il ne t'a pas oublié.]", ui.PURPLE)

    def interact(self) -> None:
        p = self.player
        feat = self.dungeon.feature_at(p.x, p.y)
        if feat is None:
            for dx, dy in DIRS[:4]:
                f2 = self.dungeon.feature_at(p.x + dx, p.y + dy)
                if f2 is not None:
                    feat = f2
                    break
        if feat is None:
            if self.dungeon.tile(p.x, p.y) == dg.STAIRS:
                self.try_descend()
                return
            self.log("Rien à toucher ici, sinon la pierre froide.", ui.MIDGREY)
            return

        if feat.kind == "chest":
            self.open_chest(feat)
        elif feat.kind == "inscription":
            self.read_inscription(feat)
        elif feat.kind == "shrine":
            self.use_shrine(feat)
        elif feat.kind == "throne":
            self.throne_attempt()

    def open_chest(self, feat) -> None:
        if feat.data.get("opened"):
            self.log("Le coffre est vide. Il l'a toujours été.", ui.MIDGREY)
            return
        feat.data["opened"] = True
        self.dungeon.set_tile(feat.x, feat.y, dg.FLOOR)
        p = self.player
        if feat.data.get("fragment"):
            p.fragments += 1
            self.log(f"Un fragment divin ! ({p.fragments}/7)", ui.YELLOW)
            self.check_fragment_bonus()
            if p.fragments == 7:
                self.log("Les sept fragments vibrent. Quelque chose s'ouvre en toi.", ui.MAGENTA)
        else:
            it = items.make_loot(self.depth, self.rng)
            msg = p.add_item(it)
            self.log(msg, ui.BONE)
        if self.rng.random() < 0.30:
            self.log("Le couvercle claque : quelque chose se réveille !", ui.RED)
            self.spawn_ambush(feat.x, feat.y)

    def spawn_ambush(self, x: int, y: int) -> None:
        pool = [m for m in ent.MONSTER_TABLE if m.depth_min <= self.depth <= m.depth_max]
        if not pool:
            return
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if self.dungeon.walkable(nx, ny) and not self.monster_at(nx, ny):
                mon = ent.Monster.from_def(self.rng.choice(pool), self.rng, self.depth)
                mon.x, mon.y = nx, ny
                mon.awake = True
                self.monsters.append(mon)
                self.log(f"{mon.name} sort de l'ombre !", ui.RED)
                return

    def read_inscription(self, feat) -> None:
        text = feat.data.get("text", "")
        new = self.mem.add_inscription(text)
        self.player.insight = self.mem.insight
        self.log("[Inscription]", ui.CYAN)
        self.log(f"« {text} »", ui.BONE)
        if new:
            self.log("Tu n'avais jamais lu cela. +1 intuition.", ui.PURPLE)
        else:
            self.log("Tu connais déjà ces mots. Ils te suivent.", ui.MIDGREY)

    def use_shrine(self, feat) -> None:
        if feat.data.get("used"):
            self.log("Le sanctuaire est froid. Il a déjà pris sa part.", ui.MIDGREY)
            return
        feat.data["used"] = True
        p = self.player
        roll = self.rng.random()
        if roll < 0.45:
            healed = p.heal(p.max_hp)
            self.log(f"Une chaleur t'envahit. +{healed} PV.", ui.GREEN)
            self.log("[Une voix] « Encore un effort, mon enfant. »", ui.PURPLE)
        elif roll < 0.65:
            p.max_hp += 2
            p.hp += 2
            self.log("Ton corps se souvient d'être plus solide. +2 PV max.", ui.GREEN)
        elif roll < 0.85:
            feat.data["used"] = True
            self.dungeon.explored |= {
                (x, y) for y in range(self.dungeon.height) for x in range(self.dungeon.width)
                if self.dungeon.tile(x, y) != dg.WALL
            }
            self.log("Tu vois la crypte entière derrière tes paupières.", ui.CYAN)
        else:
            p.hurt(4)
            p.poison = max(p.poison, 4)
            self.log("La statue sourit. Le poison entre. (-4 PV)", ui.RED)
            if p.hp <= 0:
                self.die("Châtiment du sanctuaire")

    def pickup(self) -> None:
        p = self.player
        for g in list(self.ground):
            if g["x"] == p.x and g["y"] == p.y:
                self.ground.remove(g)
                self.log(p.add_item(g["item"]), ui.BONE)
                return
        self.log("Rien à ramasser ici.", ui.MIDGREY)

    # =================================================================
    #  INVENTAIRE
    # =================================================================
    def open_inventory(self) -> None:
        p = self.player
        while True:
            body = []
            body.append(ui.paint(f" Or : {p.gold}    PV : {p.hp}/{p.max_hp}    "
                                 f"Intuition : {p.insight}", ui.GOLD))
            body.append(ui.paint(" " + "─" * 58, ui.DARKGREY))
            if not p.inventory:
                body.append("  (sac vide)")
            for idx, it in enumerate(p.inventory):
                letter = chr(ord("a") + idx)
                tag = ""
                if it is p.weapon:
                    tag = ui.paint(" [équipée]", ui.GREEN)
                elif it is p.armor:
                    tag = ui.paint(" [portée]", ui.GREEN)
                body.append(f"  {ui.paint(letter, ui.CYAN)}) "
                            f"{ui.paint(it.glyph, it.color)} {it.label}"
                            f"{tag}  {ui.paint(it.desc[:30], ui.MIDGREY)}")
            body.append(ui.paint(" " + "─" * 58, ui.DARKGREY))
            body.append(ui.paint("  Arme : " + (p.weapon.name if p.weapon else "mains nues")
                                 + "   Armure : " + (p.armor.name if p.armor else "aucune"), ui.BONE))
            body.append(ui.paint("  [a-n] examiner/équiper/boire   [ESC] fermer", ui.MIDGREY))
            key = self.modal("SAC", body, "[ESC] retour", ui.CYAN, 64).lower()
            if key == "esc" or key == "i" or key == "q":
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
        if item.kind == "weapon":
            if p.weapon is item:
                self.log(f"Tu brandis déjà {item.name}.", ui.MIDGREY)
                return
            old = p.weapon
            p.weapon = item
            self.log(f"Tu équipes {item.name} (+{item.power} dégâts).", ui.GOLD)
            if old:
                self.log(f"Tu ranges {old.name}.", ui.MIDGREY)
            return
        if item.kind == "armor":
            if p.armor is item:
                self.log("Tu portes déjà cette armure.", ui.MIDGREY)
                return
            p.armor = item
            self.log(f"Tu enfiles {item.name} (+{item.power} défense).", ui.GOLD)
            return
        if item.kind == "potion":
            self.log(f"Tu bois {item.name}.", ui.BONE)
            if "soin" in item.key:
                healed = p.heal(item.power)
                self.log(f"+{healed} PV.", ui.GREEN)
            elif "antidote" in item.key:
                p.poison = 0
                self.log("Le venin se dissout.", ui.GREEN)
            elif "vigueur" in item.key:
                p.max_hp += item.power
                p.hp += item.power
                self.log(f"+{item.power} PV max.", ui.GREEN)
            elif "sagesse" in item.key or "wisdom" in item.key:
                p.insight = min(9, p.insight + 1)
                p.max_hp = max(1, p.max_hp - 2)
                p.hp = min(p.hp, p.max_hp)
                self.log("+1 intuition. Ton corps faiblit un peu. (-2 PV max)", ui.BLUE)
            elif "brutale" in item.key or "brute" in item.key:
                p.max_hp += item.power
                p.hp += item.power
                self.log(f"+{item.power} PV max. Tes muscles hurlent.", ui.RED)
            p.remove_item(item)
            return
        if item.kind == "scroll":
            self.log(f"Tu lis {item.name}.", ui.CYAN)
            if "teleport" in item.key:
                x, y = self.dungeon.free_tile(self.rng)
                p.x, p.y = x, y
                self.update_fov()
                self.log("Le monde se plie. Tu es ailleurs.", ui.CYAN)
            elif "carto" in item.key:
                for yy in range(self.dungeon.height):
                    for xx in range(self.dungeon.width):
                        if self.dungeon.tile(xx, yy) != dg.WALL:
                            self.dungeon.explored.add((xx, yy))
                self.log("La carte du donjon s'imprime dans ton crâne.", ui.CYAN)
            elif "flammes" in item.key:
                hit = 0
                for mon in self.monsters:
                    if mon.alive and not mon.spared and (mon.x, mon.y) in self.visible:
                        if "undead" in mon.traits:
                            dmg = item.power + 4
                        else:
                            dmg = item.power
                        if mon.take_damage(dmg):
                            self.on_monster_death(mon)
                        hit += 1
                self.log(f"Le feu jaillit. {hit} créature(s) touchée(s).", ui.ORANGE)
                if hit == 0:
                    self.log("Rien ne brûle. Le parchemin se consume pour rien.", ui.MIDGREY)
            elif "frost" in item.key:
                hit = 0
                for mon in self.monsters:
                    if mon.alive and not mon.spared and (mon.x, mon.y) in self.visible:
                        dmg = item.power
                        if mon.take_damage(dmg):
                            self.on_monster_death(mon)
                        hit += 1
                self.log(f"Un vent glacial balaye la salle. {hit} créature(s) touchée(s).", ui.CYAN)
                if hit == 0:
                    self.log("Rien ne gèle. Le parchemin se consume pour rien.", ui.MIDGREY)
            elif "sleep" in item.key:
                asleep = 0
                for mon in self.monsters:
                    if mon.alive and not mon.spared and mon.x == p.x and mon.y == p.y:
                        # Sommeil local : le monstre s'endort autour du joueur
                        pass
                # Effet plus large : tous les monstres visibles s'endorment 2 tours
                for mon in self.monsters:
                    if mon.alive and not mon.spared and (mon.x, mon.y) in self.visible:
                        mon.awake = False
                        asleep += 1
                self.log(f"Les lettres dansent. {asleep} créature(s) s'endort(ent).", ui.PURPLE)
                if asleep == 0:
                    self.log("Rien ne dort. Le parchemin se consume pour rien.", ui.MIDGREY)
            p.remove_item(item)
            self.end_turn()
            return
        if item.kind == "key":
            # Vérifier si la clé est activée (7 fragments + insight 5)
            if p.fragments >= 7 and p.insight >= 5:
                self.log("La clé brille d'une lumière chaude. Elle montre le chemin.", ui.YELLOW)
                self.log("[Une voix] « Tu es prêt. Le trône t'attend. »", ui.MAGENTA)
                # Ajouter un bonus de découverte
                self.stats["secrets"] += 1
            else:
                self.log("La clé est froide. Elle ne rentre dans aucune serrure.", ui.PURPLE)
                self.log("[Une voix] « Elle te désigne. »", ui.PURPLE)
            return
        if item.kind == "fragment":
            self.log("Le fragment pulse. Il attend les six autres.", ui.YELLOW)
            return
        if item.kind == "quest":
            if "coeur" in item.key:
                self.log("Tu sens le cœur battre contre ta paume. Il t'appelle.", ui.RED)
                self.quests["heart"] = True
                self.log("[Une voix] « Ramène-le au trône. »", ui.MAGENTA)
            else:
                self.log("Il bat encore. Tu ne sais pas quoi en faire.", ui.MIDGREY)
            return
        self.log("Tu ne peux rien en faire pour l'instant.", ui.MIDGREY)

    # =================================================================
    #  AIDE
    # =================================================================
    def show_help(self) -> None:
        body = [
            ui.paint("DÉPLACEMENT", ui.GOLD, bold=True),
            "  WASD, flèches ou hjkl/yubn — se déplacer",
            "  Attaquer = marcher sur un monstre",
            "  [Entrée] ou [>] — descendre quand tu es sur un escalier",
            "  [E] — interagir (coffre, inscription, sanctuaire, trône)",
            "  [I] — sac   [G] — ramasser   [R] — attendre un tour   [Q] — quitter",
            "",
            ui.paint("SURVIVRE", ui.GOLD, bold=True),
            "  Le poison se soigne avec un antidote. Les sanctuaires guérissent… ou pas.",
            "  Chaque étage cache un fragment divin dans un coffre.",
            "  Les sept fragments ouvrent la fin secrète.",
            "",
            ui.paint("LA MÉMOIRE", ui.GOLD, bold=True),
            "  Chaque mort est enregistrée. Ton squelette revient avec ton ancienne",
            "  arme. Les inscriptions lues restent lues. L'intuition s'accumule.",
            "  Cinq fins sont possibles. La vérité demande de la mémoire.",
        ]
        self.modal("AIDE", body, "[ESC] retour", ui.GOLD, 72)

    # =================================================================
    #  ÉVÉNEMENTS
    # =================================================================
    def random_event(self) -> None:
        roll = self.rng.random()
        if roll < 0.28:
            self.log(self.rng.choice(lore.WHISPERS), ui.PURPLE)
        elif roll < 0.42:
            self.event_ghost()
        elif roll < 0.54:
            self.event_old_corpse()
        elif roll < 0.68:
            self.event_merchant()
        elif roll < 0.80:
            self.event_beggar()
        elif roll < 0.92:
            self.event_cache()
        else:
            self.event_heart_skeleton()

    def event_heart_skeleton(self) -> None:
        """Rencontre avec un squelette qui te reconnaît — drop rare."""
        p = self.player
        if not self.mem.deaths:
            return
        self.log("[Un squelette t'observe depuis le coin de l'œil.]", ui.BONE)
        self.log("« Tu as changé », dit-il. « Mais tu ne te souviens pas encore. »", ui.CYAN)
        if self.ask_confirm("Lui parler ? (o/n)"):
            p.insight = min(9, p.insight + 1)
            self.log("+1 intuition. Tu te souviens d'un visage.", ui.PURPLE)
            # Drop le cœur si pas déjà eu
            if "heart" not in self.quests:
                heart = items.make_quest_heart()
                self.ground.append({"x": p.x, "y": p.y, "item": heart})
                self.log("Le squelette te tend quelque chose. Un cœur ?", ui.RED)

    def event_ghost(self) -> None:
        p = self.player
        self.log("[Un fantôme se matérialise.]", ui.CYAN)
        if len(self.mem.deaths) == 0:
            self.log("« Tu n'es encore personne », souffle-t-il, déçu.", ui.MIDGREY)
            return
        last = self.mem.last_death() or {}
        self.log(f"« Tu étais là, quand tu es mort à l'étage {last.get('floor')}. »", ui.PURPLE)
        if self.ask_confirm("Le fantôme tend une main froide. La toucher ? (o/n)"):
            healed = p.heal(6)
            p.insight = min(9, p.insight + 1)
            self.log(f"Un froid bienfaisant. +{healed} PV, +1 intuition.", ui.CYAN)
        else:
            self.log("Le fantôme s'efface sans bruit.", ui.MIDGREY)

    def event_old_corpse(self) -> None:
        record = self.mem.last_death()
        if not record:
            self.log("Un cadavre anonyme pourrit contre le mur.", ui.MIDGREY)
            return
        self.log("[Un cadavre porte tes vêtements.]", ui.RED)
        self.log(f"Cause de la mort : {record.get('cause')}.", ui.RED)
        drops = self._gear_from_record(record)
        for i, it in enumerate(drops[:1]):
            self.ground.append({"x": self.player.x, "y": self.player.y, "item": it})
            self.log(f"Objet récupérable ici : {it.name}.", ui.GOLD)
        if not drops:
            self.player.gold += 5
            self.log("Il reste 5 pièces dans sa poche.", ui.GOLD)

    def event_merchant(self) -> None:
        p = self.player
        self.log("[Un marchand maudit émerge de l'ombre.]", ui.GOLD)
        stock = items.random_vendor_stock(self.depth, self.rng)
        price = 8 + stock.power * 3 + self.depth * 4
        self.log(f"« {stock.label} ? {price} pièces. Ne demande pas d'où ça vient. »", ui.BONE)
        if p.gold >= price:
            if self.ask_confirm(f"Acheter {stock.label} pour {price} pièces ? (o/n)"):
                p.gold -= price
                self.log(p.add_item(stock), ui.GOLD)
                if self.rng.random() < 0.30:
                    p.poison = max(p.poison, 3)
                    self.log("La marchandise est maudite. Le venin monte.", ui.RED)
                return
        else:
            self.log("Tu n'as pas assez d'or. Il hausse les épaules.", ui.MIDGREY)
        self.log("Le marchand s'éloigne en riant sans bruit.", ui.MIDGREY)

    def event_beggar(self) -> None:
        p = self.player
        self.log("[Un squelette mendie, agenouillé.]", ui.BONE)
        self.log("« Une pièce, pour un mort. Une seule. »", ui.BONE)
        if p.gold >= 10 and self.ask_confirm("Donner 10 pièces d'or ? (o/n)"):
            p.gold -= 10
            gift = items.make_potion(self.rng)
            self.log(f"Il te donne {gift.name} en échange.", ui.GOLD)
            p.add_item(gift)
            if self.mem.add_inscription("« Tu as donné à un mort. Les morts comptent. »"):
                p.insight = self.mem.insight
                self.log("+1 intuition. Tu te souviens d'un autre mendiant.", ui.PURPLE)
        else:
            self.log("Il hoche son crâne vide et retourne à son silence.", ui.MIDGREY)

    def event_cache(self) -> None:
        self.log("[Une cache dissimulée dans la pierre.]", ui.GOLD)
        gold = 6 + self.rng.randint(0, 8) + self.depth * 3
        self.player.gold += gold
        self.log(f"Tu trouves {gold} pièces d'or.", ui.GOLD)
        if self.rng.random() < 0.35:
            it = items.make_loot(self.depth, self.rng)
            self.log(self.player.add_item(it), ui.BONE)

    # =================================================================
    #  TRÔNE / FINS
    # =================================================================
    def throne_attempt(self) -> None:
        if self.boss and self.boss.alive and not self.boss.spared:
            self.log("Nhal'Zor est encore là. Il t'attend, immobile.", ui.MAGENTA)
            self.log("« Viens », dit-il. « Tu es en retard. »", ui.MAGENTA)
            return
        self.choose_ending()

    def choose_ending(self) -> None:
        p = self.player
        options = [
            ("1", "sacrifice", "Le Sacrifice — détruire Nhal'Zor et mourir avec lui"),
            ("2", "dieu", "Le Nouveau Dieu — prendre sa place sur le trône"),
            ("3", "trahison", "La Trahison — le libérer et le servir"),
        ]
        if p.insight >= 5:
            options.append(("4", "verite", "La Vérité — regarder ce que tu es vraiment"))
        if p.fragments >= 7:
            options.append(("5", "secret", "Briser le cycle — les sept fragments divins"))
        while True:
            body = [ui.paint("Le trône est là. Il n'attend que toi.", ui.MAGENTA), ""]
            for key, _, label in options:
                body.append(f"  {ui.paint('[' + key + ']', ui.GOLD)} {label}")
            body.append("")
            body.append(ui.paint(f"  Intuition : {p.insight}/5   Fragments : {p.fragments}/7",
                                 ui.MIDGREY))
            choice = self.modal("LE TRÔNE DU NÉANT", body,
                                "[ESC] reculer encore un peu", ui.MAGENTA, 70).lower()
            if choice == "esc":
                return
            for key, ending, _ in options:
                if choice == key:
                    self.ending = ending
                    self.mem.record_ending(ending)
                    return

    # =================================================================
    #  MORTS / FINS (écrans)
    # =================================================================
    def death_screen(self) -> bool:
        p = self.player
        last = self.mem.last_death() or {}
        body = ["",
                ui.paint("« Tu es déjà venu ici. Tu es déjà mort ici. »", ui.PURPLE),
                "",
                ui.paint(f"Tu meurs à l'étage {self.depth} — {self.dead_cause}.", ui.RED),
                f"Niveau {p.level}   ·   {p.kills} créatures tuées   ·   {p.gold} pièces d'or",
                f"Fragments portés : {p.fragments}/7",
                ]
        if self.dead_cause == "Abandon":
            body = ["", ui.paint("Tu reposes ton arme. La crypte attendra.", ui.MIDGREY)]
        body += ["",
                 ui.paint("─" * 58, ui.DARKGREY),
                 ui.paint(f"Le donjon enregistre ta {len(self.mem.deaths)}re mort.", ui.BONE),
                 ui.paint("Ton squelette reviendra à cet étage, avec ton équipement.", ui.BONE),
                 ui.paint(f"Intuition conservée : {self.mem.insight}", ui.CYAN),
                 ""]
        key = self.modal("MORT", body, "[Entrée] se réveiller dans la cellule   ·   [Q] quitter",
                         ui.RED, 72).lower()
        return not (key == "q" or key == "esc")

    def ending_screen(self, key: str) -> bool:
        data = lore.ENDING_TEXTS[key]
        colour = int(data["colour"])
        body = [""]
        for line in data["lines"]:
            body.append(ui.paint(line, ui.BONE) if line else "")
        body.append("")
        body.append(ui.paint("─" * 58, ui.DARKGREY))
        body.append(ui.paint(lore.ENDING_JOURNAL[key], ui.GOLD))
        found = len(self.mem.endings)
        body.append(ui.paint(f"Fins découvertes : {found}/5   ·   Cycles vécus : "
                             f"{self.mem.cycle}", ui.MIDGREY))
        if found < 5:
            body.append(ui.paint("D'autres vérités dorment dans la crypte.", ui.PURPLE))
        body.append("")
        k = self.modal(str(data["title"]), body,
                       "[Entrée] revenir au seuil   ·   [Q] quitter", colour, 72).lower()
        return not (k == "q" or k == "esc")

    # =================================================================
    #  BOUCLE PRINCIPALE
    # =================================================================
    def run(self) -> None:
        self.term.clear()
        if not self.title_screen():
            return
        while True:
            self.new_run()
            self.quit_run = False
            outcome, detail = self.play()
            self.mem.save()
            if outcome == "quit":
                return
            if outcome == "dead":
                again = self.death_screen()
            else:
                again = self.ending_screen(detail)
            if not again:
                return
            if not self.title_screen():
                return
