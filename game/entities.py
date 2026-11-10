"""Joueur et monstres."""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field

from . import items, ui


@dataclass
class MonsterDef:
    name: str
    glyph: str
    color: int
    hp: int
    atk: int
    xp: int
    depth_min: int
    depth_max: int
    traits: tuple[str, ...] = ()
    boss: bool = False


MONSTER_TABLE: list[MonsterDef] = [
    # Étage 1 — cellules
    MonsterDef("Rat géant", "r", ui.BROWN, 5, 3, 4, 1, 2),
    MonsterDef("Prisonnier mort", "p", ui.MIDGREY, 7, 3, 5, 1, 2, ("undead",)),
    MonsterDef("Gardien squelette", "z", ui.BONE, 10, 4, 8, 1, 3, ("undead",)),
    # Nouvelles créatures étage 1
    MonsterDef("Rat vétéran", "r", ui.ORANGE, 8, 4, 6, 1, 2, ("fast",)),
    MonsterDef("Ombre prisonnière", "o", ui.DARKGREY, 6, 5, 7, 1, 2, ("drain",)),
    # Étage 2 — forêt
    MonsterDef("Champignon vivant", "m", ui.MAGENTA, 8, 4, 7, 2, 3, ("poison",)),
    MonsterDef("Araignée mutante", "s", ui.PURPLE, 9, 5, 9, 2, 4, ("poison",)),
    MonsterDef("Plante carnivore", "P", ui.GREEN, 14, 6, 12, 2, 4, ()),
    # Nouvelles créatures étage 2
    MonsterDef("Bête des racines", "B", ui.BROWN, 16, 7, 14, 2, 4, ()),
    MonsterDef("Champignon géant", "M", ui.MAGENTA, 12, 5, 10, 2, 3, ("poison",)),
    # Étage 3 — cité
    MonsterDef("Marchand noyé", "M", ui.CYAN, 12, 6, 11, 3, 5, ("undead",)),
    MonsterDef("Automate nain", "A", ui.ORANGE, 20, 7, 16, 3, 5, ()),
    MonsterDef("Spectre nain", "d", ui.BLUE, 14, 8, 14, 3, 6, ("undead", "drain")),
    # Nouvelles créatures étage 3
    MonsterDef("Noyé vétéran", "n", ui.CYAN, 18, 8, 15, 3, 5, ("undead",)),
    MonsterDef("Écho aquatique", "e", ui.BLUE, 10, 9, 12, 3, 5, ("drain",)),
    # Étage 4 — bibliothèque
    MonsterDef("Livre hurlant", "b", ui.BONE, 12, 7, 13, 4, 6, ()),
    MonsterDef("Bibliothécaire mort", "L", ui.PURPLE, 18, 9, 18, 4, 6, ("undead", "drain")),
    MonsterDef("Ombre lectrice", "w", ui.DARKGREY, 22, 11, 22, 4, 7, ("drain",)),
    # Nouvelles créatures étage 4
    MonsterDef("Grimoire errant", "g", ui.YELLOW, 16, 8, 16, 4, 6, ()),
    MonsterDef("Scribe fantôme", "s", ui.CYAN, 20, 10, 20, 4, 7, ("drain",)),
    # Étage 5 — forges
    MonsterDef("Démon mineur", "D", ui.BRIGHTRED, 24, 11, 22, 5, 7, ()),
    MonsterDef("Forgeron immortel", "S", ui.ORANGE, 30, 10, 26, 5, 7, ()),
    MonsterDef("Chien de magma", "h", ui.RED, 20, 13, 20, 5, 7, ("fast",)),
    # Nouvelles créatures étage 5
    MonsterDef("Démon vétéran", "D", ui.BRIGHTRED, 32, 13, 28, 5, 7, ()),
    MonsterDef("Esprit de la forge", "E", ui.YELLOW, 26, 12, 24, 5, 7, ("drain",)),
    # Étage 6 — sanctuaire
    MonsterDef("Statue vivante", "T", ui.GREY, 34, 12, 30, 6, 7, ()),
    MonsterDef("Ange déchu", "a", ui.YELLOW, 28, 14, 32, 6, 7, ("drain",)),
    MonsterDef("Prêtre du Néant", "P", ui.PURPLE, 26, 15, 30, 6, 7, ("poison",)),
    # Nouvelles créatures étage 6
    MonsterDef("Séraphin brisé", "S", ui.WHITE, 40, 16, 38, 6, 7, ("drain",)),
    MonsterDef("Disciple du vide", "d", ui.PURPLE, 30, 14, 34, 6, 7, ("poison",)),
    # Étage 7 — trône
    MonsterDef("Horreur du vide", "V", ui.PURPLE, 40, 16, 40, 7, 7, ("drain",)),
    MonsterDef("Écho de toi-même", "e", ui.WHITE, 36, 18, 44, 7, 7, ("fast",)),
    # Nouvelles créatures étage 7
    MonsterDef("Reflet déformé", "R", ui.MAGENTA, 44, 20, 48, 7, 7, ("drain", "fast")),
]

BOSSES = {
    3: MonsterDef("Roi Nain Maudit", "K", ui.ORANGE, 55, 9, 60, 3, 3, ("undead",), True),
    5: MonsterDef("Seigneur des Forges", "F", ui.BRIGHTRED, 75, 12, 90, 5, 5, (), True),
    6: MonsterDef("Gardien du Sanctuaire", "G", ui.YELLOW, 90, 14, 110, 6, 6, ("drain",), True),
    7: MonsterDef("NHAL'ZOR, LE DIEU DU NÉANT", "Ω", ui.MAGENTA, 160, 18, 250, 7, 7,
                  ("drain", "poison"), True),
}


# Définitions des classes disponibles au départ
CLASS_DEFS = {
    "gardien": {
        "name": "Gardien",
        "hp_bonus": 4,
        "atk_bonus": 1,
        "armor_item": "cuir",
        "insight_bonus": 0,
        "scroll_item": None,
    },
    "rodeur": {
        "name": "Rôdeur",
        "hp_bonus": 0,
        "atk_bonus": 1,
        "armor_item": None,
        "insight_bonus": 1,
        "scroll_item": None,
    },
    "sorcier": {
        "name": "Sorcier",
        "hp_bonus": -2,
        "atk_bonus": 0,
        "armor_item": None,
        "insight_bonus": 1,
        "scroll_item": "flammes",
    },
}


@dataclass
class Monster:
    name: str
    glyph: str
    color: int
    hp: int
    max_hp: int
    atk: int
    xp: int
    traits: frozenset[str] = frozenset()
    boss: bool = False
    x: int = 0
    y: int = 0
    alive: bool = True
    awake: bool = False
    spared: bool = False
    drops: list = field(default_factory=list)
    instance_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    loot_generated: bool = False

    @classmethod
    def from_def(cls, d: MonsterDef, rng: random.Random, depth: int) -> "Monster":
        scale = 1.0 + 0.06 * max(0, depth - d.depth_min)
        hp = max(1, int(d.hp * scale))
        return cls(d.name, d.glyph, d.color, hp, hp, d.atk, d.xp,
                   frozenset(d.traits), d.boss)

    @property
    def is_undead(self) -> bool:
        return "undead" in self.traits

    def take_damage(self, amount: int) -> bool:
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
            return True
        return False


class Player:
    def __init__(self, memory=None, class_key: str = "gardien") -> None:
        self.name = "l'Aventurier"
        self.class_key = class_key
        # Base stats modifiés par la classe
        hp_mod = CLASS_DEFS[class_key]["hp_bonus"] if class_key in CLASS_DEFS else 0
        atk_mod = CLASS_DEFS[class_key]["atk_bonus"] if class_key in CLASS_DEFS else 0
        self.max_hp = 22 + hp_mod
        self.hp = self.max_hp
        self.level = 1
        self.xp = 0
        self.base_atk = 3 + atk_mod
        self.base_def = 0
        from .item_manager import Equipment, Inventory
        self.weapon: items.Item | None = None
        self.armor: items.Item | None = None
        self.inventory = Inventory(owner="player", capacity=20)
        self.equipment = Equipment(owner="player")
        self.gold = 0
        self.poison = 0
        self.fragments = 0
        self.kills = 0
        self.insight = 0
        self.cycle = 1
        # Compétences débloquées
        self.unlocked_skills: set[str] = set()
        # Dernier souffle (résurrection)
        self.has_last_breath = False
        if memory is not None:
            self.insight = min(9, getattr(memory, "insight", 0))
            self.cycle = getattr(memory, "cycle", 1)
            # Appliquer les compétences mémorisées
            self._apply_insight_skills()
        # Équipement de classe par défaut
        if class_key in CLASS_DEFS:
            cdef = CLASS_DEFS[class_key]
            if cdef["armor_item"]:
                for key, aname, glyph, color, power, desc in items.ARMORS:
                    if key == cdef["armor_item"]:
                        self.armor = items.Item(f"a_{key}", aname, glyph, color, "armor", power, desc)
                        break
            if cdef["scroll_item"]:
                for key, sname, glyph, color, power, desc, effect in items.SCROLLS:
                    if key == cdef["scroll_item"]:
                        self.inventory.append(items.Item(f"s_{key}", sname, glyph, color, "scroll", power, desc))
                        break
        self.inventory.append(items.make_black_key())
        # Un souvenir ramené du cycle précédent
        if self.insight >= 6:
            self.max_hp += 4
            self.hp = self.max_hp

    def _apply_insight_skills(self) -> None:
        """Applique les compétences basées sur l'intuition persistante."""
        from . import lore
        for threshold, skill in lore.SKILLS.items():
            if self.insight >= threshold:
                self.unlocked_skills.add(skill["effect"])

    # ------------------------------------------------------------- combat
    @property
    def attack(self) -> int:
        w = self.weapon.power if self.weapon else 2
        return w + self.base_atk + (self.level - 1) + self.equipment.stat("dmg")

    @property
    def defense(self) -> int:
        slots = sum(int(it.power) for slot, it in self.equipment.slots.items()
                    if slot not in ("weapon", "ring1", "ring2", "amulet", "hands"))
        return ((self.armor.power if self.armor else 0) + self.base_def
                + slots + self.equipment.stat("defense") // 2)

    def damage_roll(self, rng: random.Random) -> int:
        base = self.attack
        roll = rng.randint(max(1, base - 2), base + 2)
        return max(1, roll)

    def hurt(self, amount: int) -> None:
        self.hp = max(0, self.hp - max(0, amount))

    @property
    def alive(self) -> bool:
        return self.hp > 0

    @property
    def xp_needed(self) -> int:
        return 18 + (self.level - 1) * 22

    def gain_xp(self, amount: int) -> list[str]:
        self.xp += amount
        notes = []
        while self.xp >= self.xp_needed:
            self.xp -= self.xp_needed
            self.level += 1
            self.max_hp += 6
            self.hp = min(self.max_hp, self.hp + 6)
            self.base_atk += 1
            notes.append(f"Tu atteins le niveau {self.level}. Ton corps se souvient.")
        return notes

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    # ---------------------------------------------------------- inventaire
    def add_item(self, item: items.Item) -> str:
        if item.kind == "gold":
            from .item_manager import MANAGER
            MANAGER.destroy(item)
            self.gold += item.power
            return f"{item.power} pièces d'or."
        if item.kind == "fragment":
            from .item_manager import MANAGER
            MANAGER.destroy(item)
            self.fragments += item.power
            return f"Un fragment divin ! ({self.fragments}/7)"
        msg = self.inventory.add(item)
        if msg.startswith("Tu ramasses"):
            return msg
        return msg

    def remove_item(self, item: items.Item) -> None:
        item.stack -= 1
        if item.stack <= 0 and item in self.inventory:
            self.inventory.remove(item)

    def equipment_summary(self) -> tuple[str, str]:
        w = self.weapon.name if self.weapon else "mains nues"
        a = self.armor.name if self.armor else "aucune"
        return w, a
