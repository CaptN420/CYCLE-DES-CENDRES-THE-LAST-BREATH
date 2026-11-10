"""Intégration du familier dans une partie : état, butin, tours, menus.

Mixin partagé par les trois chapitres. L'hôte doit fournir :
    self.player, self.monsters, self.dungeon, self.ground, self.rng, self.log,
    self.modal(title, body, footer, colour, width), self.mem
et peut surcharger `_fam_depth()` / `_fam_ask()` / `_fam_boss_reward()`.
"""
from __future__ import annotations

from . import familiar as fam_mod
from . import familiar_ai, item_db, item_manager, loot_manager, ui

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]


class FamiliarField:
    FAM_BLOCKED = ("THE AUTHOR",)

    # ------------------------------------------------------------ helpers
    def _fam_depth(self) -> int:
        depth = getattr(self, "depth", None)
        if isinstance(depth, int) and depth > 0:
            return depth
        key = getattr(self, "territory_key", None)
        try:
            from . import lore3
            for idx, terr in enumerate(lore3.TERRITORIES):
                if terr.key == key:
                    return idx + 1
        except Exception:
            pass
        return 3

    def _fam_ask(self, prompt: str) -> bool:
        for name in ("ask", "ask_confirm"):
            fn = getattr(self, name, None)
            if callable(fn):
                return bool(fn(prompt))
        return False

    def _fam_boss_reward(self, mon, killer: str) -> None:
        fn = getattr(self, "boss_reward", None)
        if not callable(fn):
            return
        try:
            fn(mon, killer=killer)
        except TypeError:
            fn(mon)

    # ------------------------------------------------------------- état
    def load_familiar(self) -> None:
        data = self.mem.data.get("familiar")
        try:
            fam = fam_mod.Familiar.from_dict(data) if data else fam_mod.default_familiar("loup")
        except Exception:
            fam = fam_mod.default_familiar("loup")
        self.familiar = fam
        fam.x = fam.y = 0

    def save_familiar(self) -> None:
        if getattr(self, "familiar", None) is None:
            return
        self.mem.data["familiar"] = self.familiar.to_dict()
        self.mem.save()

    def place_familiar(self, px: int, py: int) -> None:
        fam = getattr(self, "familiar", None)
        if fam is None or getattr(self, "dungeon", None) is None:
            return
        for dx, dy in DIRS:
            nx, ny = px + dx, py + dy
            if self.dungeon.walkable(nx, ny) and not self.monster_at(nx, ny):
                fam.x, fam.y = nx, ny
                return
        fam.x, fam.y = px, py

    # ------------------------------------------------------------ butin
    def familiar_pickup(self) -> None:
        fam = getattr(self, "familiar", None)
        if fam is None or not fam.alive:
            return
        for entry in list(self.ground):
            item = entry["item"]
            if (entry["x"], entry["y"]) != (fam.x, fam.y) or item.owner != "familiar":
                continue
            self.ground.remove(entry)
            self.log(fam.loot(item), ui.CYAN)
            for note in fam.equip_best():
                self.log(note, ui.GREEN)
            self.save_familiar()

    def familiar_attack(self, mon, bonus: int = 0, bleed: bool = False) -> None:
        fam = getattr(self, "familiar", None)
        if fam is None or not fam.alive:
            return
        if mon.name in self.FAM_BLOCKED:
            self.log(f"{fam.name} frappe l'air : quelque chose réécrit le geste.", ui.WHITE)
            return
        dmg = max(1, fam.attack + bonus + self.rng.randint(-2, 2))
        killed = mon.take_damage(dmg)
        self.log(f"{fam.name} frappe {mon.name} : {dmg} dégâts.", ui.CYAN)
        if killed:
            self.on_familiar_kill(mon)

    def on_familiar_kill(self, mon) -> None:
        fam = getattr(self, "familiar", None)
        if fam is None:
            return
        fam.kills += 1
        self.log(f"{mon.name} tombe sous les coups de {fam.name}.", ui.CYAN)
        for note in fam.gain_xp(max(1, mon.xp // 2 + 2)):
            self.log(note, ui.GREEN)
        drops = loot_manager.roll_loot(mon, "familiar", self._fam_depth(), self.rng, chance=0.55)
        for item in drops:
            self.ground.append({"x": mon.x, "y": mon.y, "item": item})
        if drops:
            self.log("Son butin lui revient — tu n'y touches pas.", ui.MIDGREY)
        if getattr(mon, "boss", False):
            self._fam_boss_reward(mon, "familiar")
        self.save_familiar()

    def familiar_reveal(self) -> None:
        fam = getattr(self, "familiar", None)
        if fam is None or self.dungeon is None:
            return
        for y in range(max(0, fam.y - 9), min(self.dungeon.height, fam.y + 10)):
            for x in range(max(0, fam.x - 9), min(self.dungeon.width, fam.x + 10)):
                if self.dungeon.tile(x, y) != 0:
                    self.dungeon.explored.add((x, y))
        if hasattr(self, "update_fov"):
            self.update_fov()

    # -------------------------------------------------------- monstres
    def _target_of(self, mon):
        p = self.player
        fam = getattr(self, "familiar", None)
        if fam is None or not fam.alive:
            return p.x, p.y, False
        d_player = abs(mon.x - p.x) + abs(mon.y - p.y)
        d_fam = abs(mon.x - fam.x) + abs(mon.y - fam.y)
        if getattr(self, "fam_taunt", 0) > 0 and d_fam <= d_player + 3:
            return fam.x, fam.y, True
        if d_fam <= 1 and d_player > 2 and self.rng.random() < 0.4:
            return fam.x, fam.y, True
        return p.x, p.y, False

    def monster_attack_familiar(self, mon) -> None:
        fam = getattr(self, "familiar", None)
        if fam is None or not fam.alive:
            return
        raw = self.rng.randint(max(1, mon.atk - 3), mon.atk + 1)
        note = fam.take_damage(raw)
        self.log(note, ui.RED if fam.alive else ui.MAGENTA)
        if not fam.alive:
            self.log(f"{fam.name} est hors combat. Il reviendra dans quelques tours.", ui.PURPLE)
            self.save_familiar()

    # -------------------------------------------------------- interface
    def _fam_body(self) -> list[str]:
        fam = self.familiar
        evo = fam.next_evolution
        body = [ui.paint(f" {fam.display_name()}   Niveau {fam.level}", ui.CYAN, bold=True),
                f" Classe : {fam.cdef['name']}   Ordre : {fam.order}",
                f" Expérience : {fam.xp} / {fam.xp_needed}"
                + (f"   (évolution niv. {evo[0]} : {evo[1]})" if evo else "   (forme finale)"),
                f" PV : {fam.hp}/{fam.max_hp}"
                + (f"   MANA : {fam.mana}/{fam.max_mana}" if fam.max_mana else ""),
                f" ATK : {fam.attack}   DEF : {fam.armor_value}   Vitesse : {fam.speed_value}",
                f" Butins ramassés : {fam.loot_taken}   Ennemis tués : {fam.kills}"
                + ("" if fam.alive else "   HORS COMBAT"),
                ui.paint(" " + "─" * 58, ui.DARKGREY),
                ui.paint("  ÉQUIPEMENT", ui.GOLD, bold=True)]
        for slot in fam.equipment.SLOTS:
            item = fam.equipment.get(slot)
            body.append(f"   {item_db.SLOT_FR.get(slot, slot):<11} : "
                        + (ui.paint(item.label, item_db.rarity_color(item.rarity)) if item else "—"))
        body.append(ui.paint(f"  SAC : {len(fam.inventory)}/{fam.inventory.capacity} objets", ui.MIDGREY))
        body.append(ui.paint(" " + "─" * 58, ui.DARKGREY))
        body.append(ui.paint(f" Dernier événement : {fam.history[-1] if fam.history else '—'}", ui.MIDGREY))
        return body

    def companion_menu(self) -> None:
        while True:
            fam = getattr(self, "familiar", None)
            if fam is None or getattr(self, "player", None) is None:
                return
            key = self.modal(f"COMPAGNON — {fam.name}", self._fam_body(),
                             "[S] stats [E] équipement [I] sac [C] compétences [H] historique "
                             "[O] ordre [D] donner [R] prendre [F] fermer", ui.CYAN, 72).lower()
            if key in ("f", "esc", "q", "p"):
                return
            if key == "s":
                self.fam_stats()
            elif key == "e":
                self.fam_equipment()
            elif key == "i":
                self.fam_inventory()
            elif key == "c":
                self.fam_abilities()
            elif key == "h":
                body = [" " + line for line in fam.history[-16:]] or ["  (rien à raconter)"]
                self.modal("HISTORIQUE DU FAMILIER", body, "[ESC] retour", ui.CYAN, 72)
            elif key == "o":
                self.fam_orders()
            elif key == "d":
                self.transfer("donner")
            elif key == "r":
                self.transfer("prendre")

    def fam_stats(self) -> None:
        fam = self.familiar
        weights = item_db.CLASS_WEIGHTS.get(fam.class_key, {})
        body = [ui.paint(f" {fam.cdef['blurb']}", ui.MIDGREY), "",
                ui.paint("  POIDS D'ÉVALUATION (sa façon de juger un objet)", ui.GOLD)]
        for stat, weight in sorted(weights.items(), key=lambda kv: -kv[1]):
            if weight > 0:
                body.append(f"   {stat:<8} {ui.paint('█' * int(weight * 4), ui.CYAN)}")
        body.append("")
        body.append(ui.paint("  ÉVOLUTIONS", ui.GOLD))
        for threshold, name, glyph in fam_mod.EVOLUTIONS[fam.class_key]:
            mark = "✓" if fam.level >= threshold else (">" if fam.level + 3 >= threshold else "·")
            body.append(f"   {ui.paint(mark, ui.GREEN)} niv. {threshold:>2} — {name} {glyph}")
        self.modal("STATISTIQUES", body, "[ESC] retour", ui.CYAN, 72)

    def fam_equipment(self) -> None:
        fam = self.familiar
        while True:
            body = [ui.paint(f" {fam.name} — {fam.armor_value} DEF / {fam.attack} ATK", ui.CYAN), ""]
            slots = list(fam.equipment.SLOTS)
            for idx, slot in enumerate(slots):
                item = fam.equipment.get(slot)
                body.append(f" {ui.paint(chr(ord('a') + idx), ui.CYAN)}) "
                            f"{item_db.SLOT_FR.get(slot, slot):<11} : "
                            + (ui.paint(item.label, item_db.rarity_color(item.rarity)) if item else "—"))
            key = self.modal("ÉQUIPEMENT DU FAMILIER", body,
                             "[a-i] retirer un objet   [ESC] retour", ui.CYAN, 72).lower()
            if key in ("esc", "q", "f"):
                return
            idx = ord(key) - ord("a") if len(key) == 1 and "a" <= key <= "z" else -1
            if 0 <= idx < len(slots):
                _ok, msg = fam.equipment.unequip(slots[idx], fam.inventory)
                self.log(msg, ui.MIDGREY)
                self.save_familiar()

    def fam_inventory(self) -> None:
        fam = self.familiar
        while True:
            order = list(fam.inventory)
            body = [ui.paint(f" Capacité : {len(order)}/{fam.inventory.capacity}", ui.CYAN),
                    ui.paint(" " + "─" * 58, ui.DARKGREY)]
            if not order:
                body.append("  (sac vide)")
            for idx, item in enumerate(order):
                eq = any(item is it for it in fam.equipment.slots.values())
                body.append(f" {ui.paint(chr(ord('a') + idx), ui.CYAN)}) {item.label}"
                            + (ui.paint("  [équipé]", ui.GREEN) if eq else "")
                            + ui.paint(f"   valeur {fam.score(item):.0f}", ui.DARKGREY))
            body.append(ui.paint("  [E] équiper le meilleur   [U] utiliser   [J] jeter   "
                                 "[D] détruire   [R] prendre   [ESC] retour", ui.MIDGREY))
            key = self.modal("SAC DU FAMILIER", body, "[ESC] retour", ui.CYAN, 72).lower()
            if key in ("esc", "q", "f"):
                return
            if key == "e":
                for note in fam.equip_best():
                    self.log(note, ui.GREEN)
                self.save_familiar()
                continue
            if key == "r":
                self.transfer("prendre")
                continue
            if key in ("u", "j", "d"):
                if not order:
                    continue
                pick = self.modal("SAC DU FAMILIER", body,
                                  "Lettre de l'objet   [ESC] annuler", ui.CYAN, 72).lower()
                idx = ord(pick) - ord("a") if len(pick) == 1 and "a" <= pick <= "z" else -1
                if not (0 <= idx < len(order)):
                    continue
                item = order[idx]
                if key == "u":
                    self.fam_use(item)
                elif key == "j":
                    fam.inventory.remove(item)
                    item.owner = "familiar"
                    item.location = "GROUND"
                    self.ground.append({"x": fam.x, "y": fam.y, "item": item})
                    self.log(f"{fam.name} jette {item.name}.", ui.MIDGREY)
                else:
                    if self._fam_ask(f"Détruire {item.name} (familier) ? (o/n)"):
                        self.log(item_manager.destroy_item(item, fam.inventory), ui.RED)
                self.save_familiar()

    def fam_use(self, item) -> None:
        fam = self.familiar
        if item.kind == "potion" and "heal" in (item.effects or ()):
            gain = fam.heal(item.power)
            fam.inventory.remove_item(item)
            self.log(f"{fam.name} boit {item.name} (+{gain} PV).", ui.GREEN)
            self.save_familiar()
            return
        self.log(f"{fam.name} ne peut rien faire de ça maintenant.", ui.MIDGREY)

    def fam_abilities(self) -> None:
        fam = self.familiar
        body = []
        for key in fam.abilities:
            info = fam_mod.ABILITIES.get(key, {})
            cd = fam.cooldowns.get(key, 0)
            state = ui.paint("prêt", ui.GREEN) if cd == 0 else ui.paint(f"recharge {cd}", ui.RED)
            body.append(ui.paint(f"  {info.get('name', key)}", ui.GOLD, bold=True))
            body.append(f"    {info.get('desc', '')}")
            body.append(f"    coût : {info.get('cost', 0)} mana   "
                        f"recharge : {info.get('cooldown', 0)} tours   {state}")
            body.append("")
        body.append(ui.paint("  L'IA décide seule ; les ordres changent ses priorités.", ui.MIDGREY))
        self.modal("COMPÉTENCES", body, "[ESC] retour", ui.GOLD, 72)

    def fam_orders(self) -> None:
        fam = self.familiar
        keys = list(fam_mod.ORDERS)
        body = [ui.paint("  Choisir une priorité — l'IA garde son autonomie.", ui.MIDGREY), ""]
        for idx, key in enumerate(keys):
            mark = "→" if key == fam.order else " "
            body.append(f" {mark} {ui.paint(str(idx + 1), ui.CYAN)}) {key:<9} {fam_mod.ORDERS[key]}")
        key = self.modal("ORDRES", body, "[1-6] ordre   [ESC] retour", ui.CYAN, 72).lower()
        if key.isdigit() and 1 <= int(key) <= len(keys):
            fam.set_order(keys[int(key) - 1])
            self.log(f"Ordre : {keys[int(key) - 1]}.", ui.CYAN)
            self.save_familiar()

    def transfer(self, direction: str) -> None:
        """Échange explicite, jamais automatique."""
        fam = self.familiar
        p = self.player
        if direction == "donner":
            source, target, label = p.inventory, fam.inventory, "à donner au familier"
        else:
            source, target, label = fam.inventory, p.inventory, "à reprendre"
        order = list(source)
        if not order:
            self.log("Rien à échanger.", ui.MIDGREY)
            return
        body = [ui.paint(f"  Objets {label} (le joueur autorise l'échange)", ui.YELLOW), ""]
        for idx, item in enumerate(order):
            body.append(f" {ui.paint(chr(ord('a') + idx), ui.CYAN)}) {item.label}")
        key = self.modal("ÉCHANGE", body, "Lettre de l'objet   [ESC] annuler", ui.YELLOW, 72).lower()
        idx = ord(key) - ord("a") if len(key) == 1 and "a" <= key <= "z" else -1
        if not (0 <= idx < len(order)):
            return
        item = order[idx]
        item.owner = "familiar" if direction == "donner" else "player"
        source.remove(item)
        msg = target.add(item, force_owner=True)
        if msg.startswith("Cet objet") or "plein" in msg.lower() or "appartient" in msg.lower():
            source.add(item, force_owner=True)
            self.log("Échange impossible (sac plein).", ui.MIDGREY)
            return
        self.log(f"Échange accepté : {item.name}.", ui.GOLD)
        if direction == "donner":
            for note in fam.equip_best():
                self.log(note, ui.GREEN)
        self.save_familiar()

    # ------------------------------------------------------------- tour
    def familiar_turn(self) -> None:
        fam = getattr(self, "familiar", None)
        if fam is None:
            return
        if getattr(self, "fam_taunt", 0) > 0:
            self.fam_taunt -= 1
        familiar_ai.take_turn(fam, self)
        if getattr(self, "turn", 0) % 10 == 0:      # sauvegarde régulière du compagnon
            self.save_familiar()

    def familiar_cell(self, x: int, y: int, lit: bool) -> str | None:
        fam = getattr(self, "familiar", None)
        if fam is None or not fam.alive or (fam.x, fam.y) != (x, y):
            return None
        return (ui.paint(fam.glyph, fam.color, bold=lit) if lit
                else ui.paint(fam.glyph, ui.DARKGREY, dim=True))

    def familiar_status(self) -> str:
        fam = getattr(self, "familiar", None)
        if fam is None:
            return ""
        return f"   {fam.glyph} {fam.hp}/{fam.max_hp}" + ("" if fam.alive else " KO")