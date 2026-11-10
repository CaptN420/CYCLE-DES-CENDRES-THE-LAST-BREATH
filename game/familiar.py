"""Familier autonome : classes, évolution, inventaire et équipement propres."""
from __future__ import annotations

import random

from . import item_db, items, ui
from .item_manager import Equipment, Inventory

CLASSES = {
    "loup": {
        "name": "Loup", "glyph": "d", "color": ui.MIDGREY,
        "hp": 34, "atk": 9, "defense": 3, "speed": 15, "mana": 0,
        "melee": True, "ability": "morsure",
        "prefs": ("dague", "hache", "epee_courte"),
        "blurb": "Rapide, loyal, il mord avant de réfléchir.",
    },
    "golem": {
        "name": "Golem", "glyph": "G", "color": ui.BROWN,
        "hp": 62, "atk": 8, "defense": 9, "speed": 6, "mana": 0,
        "melee": True, "ability": "provocation",
        "prefs": ("epee_lourde", "hache", "lourde"),
        "blurb": "Lent. Il encaisse ce que tu ne veux pas encaisser.",
    },
    "arcaniste": {
        "name": "Arcaniste", "glyph": "a", "color": ui.PURPLE,
        "hp": 26, "atk": 6, "defense": 3, "speed": 10, "mana": 30,
        "melee": False, "ability": "eclair",
        "prefs": ("baton", "magique", "arc"),
        "blurb": "Il attaque à distance et déteste le corps à corps.",
    },
    "corbeau": {
        "name": "Corbeau", "glyph": "c", "color": ui.CYAN,
        "hp": 22, "atk": 7, "defense": 2, "speed": 20, "mana": 0,
        "melee": True, "ability": "oeil",
        "prefs": ("dague", "arc", "legere"),
        "blurb": "Il voit les pièges et les choses qu'on cache.",
    },
    "chevalier": {
        "name": "Chevalier spectral", "glyph": "K", "color": ui.BONE,
        "hp": 48, "atk": 8, "defense": 7, "speed": 9, "mana": 10,
        "melee": True, "ability": "garde",
        "prefs": ("epee_courte", "epee_lourde", "lourde", "bouclier"),
        "blurb": "Il porte une armure vide et un serment intact.",
    },
}

EVOLUTIONS = {
    "loup": [(1, "Loup des cavernes", "d"), (5, "Loup de guerre", "D"),
             (10, "Loup sanguinaire", "W"), (20, "Prédateur ancestral", "W"),
             (30, "Seigneur des ombres", "Ω")],
    "golem": [(1, "Golem de pierre", "G"), (5, "Golem de granit", "G"),
              (10, "Colosse silencieux", "C"), (20, "Sentinelle éternelle", "C"),
              (30, "Rempart du Néant", "Ω")],
    "arcaniste": [(1, "Étincelle", "a"), (5, "Arcaniste lié", "a"),
                  (10, "Mage d'Intervalle", "A"), (20, "Archonte", "A"),
                  (30, "Voix du Néant", "Ω")],
    "corbeau": [(1, "Corbeau des ombres", "c"), (5, "Corbeau noir", "c"),
                (10, "Messager des morts", "C"), (20, "Œil du gouffre", "C"),
                (30, "Aile du Néant", "Ω")],
    "chevalier": [(1, "Écuyer spectral", "K"), (5, "Chevalier spectral", "K"),
                  (10, "Chevalier de cendre", "K"), (20, "Paladin déchu", "K"),
                  (30, "Gardien du serment", "Ω")],
}

ORDERS = {
    "suivre": "reste près de toi et n'engage que le combat proche",
    "defendre": "protège le joueur en priorité",
    "agressif": "attaque tout ce qu'il voit",
    "prudent": "évite les combats, se soigne tôt",
    "reste": "garde sa position",
    "ramasser": "récupère uniquement son butin",
}

ABILITIES = {
    "morsure": {"name": "Morsure", "cost": 0, "cooldown": 4,
                "desc": "Inflige des saignements."},
    "provocation": {"name": "Provocation", "cost": 0, "cooldown": 5,
                    "desc": "Force les ennemis à le viser."},
    "eclair": {"name": "Éclair", "cost": 8, "cooldown": 3,
               "desc": "Frappe à distance (portée 5)."},
    "oeil": {"name": "Œil des ombres", "cost": 0, "cooldown": 6,
             "desc": "Révèle les passages et les pièges."},
    "garde": {"name": "Garde", "cost": 4, "cooldown": 6,
              "desc": "Annule la moitié du prochain coup porté au joueur."},
}


class Familiar:
    def __init__(self, class_key: str = "loup", name: str = "", level: int = 1):
        if class_key not in CLASSES:
            class_key = "loup"
        self.class_key = class_key
        cdef = CLASSES[class_key]
        self.name = name or cdef["name"]
        self.level = max(1, int(level))
        self.xp = 0
        self.max_hp = cdef["hp"] + (self.level - 1) * 5
        self.hp = self.max_hp
        self.atk = cdef["atk"] + (self.level - 1)
        self.defense = cdef["defense"] + (self.level - 1) // 2
        self.speed = cdef["speed"]
        self.max_mana = cdef["mana"] + (self.level - 1) * 3
        self.mana = self.max_mana
        self.inventory = Inventory(owner="familiar", capacity=12)
        self.equipment = Equipment(owner="familiar")
        self.order = "suivre"
        self.history: list[str] = []
        self.cooldowns: dict[str, int] = {}
        self.kills = 0
        self.loot_taken = 0
        self.ko_turns = 0
        self.x = 0
        self.y = 0
        self.alive = True
        self.abilities = [cdef["ability"]]
        self.target_id = ""
        self.add_history(f"{self.display_name()} te suit depuis l'Intervalle.")

    # ------------------------------------------------------------ identité
    @property
    def cdef(self) -> dict:
        return CLASSES[self.class_key]

    @property
    def glyph(self) -> str:
        for threshold, _name, glyph in EVOLUTIONS[self.class_key]:
            if self.level >= threshold:
                current = glyph
        return current

    def display_name(self) -> str:
        name = self.cdef["name"]
        for threshold, evo, _glyph in EVOLUTIONS[self.class_key]:
            if self.level >= threshold:
                name = evo
        return f"{self.name} ({name})"

    @property
    def evolution_stage(self) -> str:
        name = self.cdef["name"]
        for threshold, evo, _glyph in EVOLUTIONS[self.class_key]:
            if self.level >= threshold:
                name = evo
        return name

    @property
    def color(self) -> int:
        return self.cdef["color"]

    @property
    def xp_needed(self) -> int:
        return 20 + (self.level - 1) * 25

    @property
    def next_evolution(self) -> tuple[int, str] | None:
        for threshold, evo, _glyph in EVOLUTIONS[self.class_key]:
            if threshold > self.level:
                return threshold, evo
        return None

    # ------------------------------------------------------------ stats
    @property
    def attack(self) -> int:
        base = self.atk + self.equipment.stat("dmg")
        weapon = self.equipment.get("weapon")
        if weapon is not None and weapon.kind == "weapon":
            base += max(0, weapon.power - self.atk // 2)
        return base

    @property
    def armor_value(self) -> int:
        base = self.defense + self.equipment.stat("defense")
        chest = self.equipment.get("chest")
        if chest is not None:
            base += chest.power // 2
        return base

    @property
    def speed_value(self) -> int:
        return self.speed + self.equipment.stat("speed")

    def score(self, item: items.Item) -> float:
        return item_db.item_score(item, self.class_key)

    def take_damage(self, amount: int) -> str:
        dmg = max(1, amount - self.armor_value // 2)
        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.ko_turns = 12
            self.add_history("Il tombe. Son corps se dissout à moitié.")
            return f"{self.name} s'effondre (hors combat)."
        return f"{self.name} encaisse {dmg} dégâts."

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def gain_xp(self, amount: int) -> list[str]:
        notes: list[str] = []
        if not self.alive:
            return notes
        self.xp += max(0, amount)
        while self.xp >= self.xp_needed:
            self.xp -= self.xp_needed
            self.level += 1
            self.max_hp += 5
            self.atk += 1
            if self.level % 2 == 0:
                self.defense += 1
            if self.max_mana:
                self.max_mana += 3
            self.hp = self.max_hp
            self.mana = self.max_mana
            notes.append(f"{self.name} atteint le niveau {self.level}.")
            for threshold, evo, _glyph in EVOLUTIONS[self.class_key]:
                if threshold == self.level:
                    notes.append(f"ÉVOLUTION : {self.name} devient {evo}.")
                    self.add_history(f"Évolution : {evo}.")
        return notes

    # ------------------------------------------------------ inventaire
    def loot(self, item: items.Item) -> str:
        if item.owner not in ("familiar", "none", ""):
            return "Ce butin n'est pas le sien."
        msg = self.inventory.add(item)
        if msg.startswith("Tu ramasses"):
            self.loot_taken += 1
            self.add_history(f"Butin : {item.name}.")
        return msg

    def equip_best(self) -> list[str]:
        """Équipe automatiquement la meilleure pièce disponible pour sa classe."""
        notes: list[str] = []
        for item in sorted(list(self.inventory), key=lambda it: -self.score(it)):
            if not item.slot:
                continue
            current = self.equipment.get(item.slot)
            if current is not None and self.score(item) <= self.score(current):
                continue
            if item.slot == "weapon" and self.class_key == "arcaniste":
                if item.base_key not in ("baton", "arc"):
                    continue
            ok, msg = self.equipment.equip(item, self.inventory)
            if ok:
                notes.append(msg)
                self.add_history(f"Équipé : {item.name}.")
        return notes

    def drink(self) -> str | None:
        if self.hp >= self.max_hp * 0.5:
            return None
        candidates = [it for it in self.inventory
                      if it.kind == "potion" and ("heal" in it.effects or "soin" in it.key)]
        if not candidates:
            return None
        potion = max(candidates, key=lambda it: it.power)
        gain = self.heal(potion.power)
        self.inventory.remove_item(potion)
        self.add_history(f"A bu {potion.name} (+{gain} PV).")
        return f"{self.name} boit {potion.name} (+{gain} PV)."

    def restock_mana(self) -> str | None:
        if self.max_mana == 0 or self.mana > self.max_mana * 0.3:
            return None
        for it in list(self.inventory):
            if it.kind == "potion" and "mana" in it.effects:
                self.mana = min(self.max_mana, self.mana + it.power)
                self.inventory.remove_item(it)
                return f"{self.name} récupère de la mana."
        return None

    # ------------------------------------------------------------ ordres
    def set_order(self, order: str) -> bool:
        if order not in ORDERS:
            return False
        self.order = order
        self.add_history(f"Ordre reçu : {order}.")
        return True

    def add_history(self, text: str) -> None:
        self.history.append(text)
        if len(self.history) > 60:
            self.history = self.history[-60:]

    # ------------------------------------------------------------ KO
    def tick_ko(self) -> str | None:
        if self.alive:
            return None
        self.ko_turns -= 1
        if self.ko_turns <= 0:
            self.alive = True
            self.hp = max(1, self.max_hp // 3)
            self.add_history("Il se relève, à moitié.")
            return f"{self.name} se relève."
        return None

    # ------------------------------------------------------- sauvegarde
    def to_dict(self) -> dict:
        return {
            "name": self.name, "class_key": self.class_key, "level": self.level,
            "xp": self.xp, "hp": self.hp, "max_hp": self.max_hp, "atk": self.atk,
            "defense": self.defense, "speed": self.speed, "mana": self.mana,
            "max_mana": self.max_mana, "order": self.order,
            "kills": self.kills, "loot_taken": self.loot_taken,
            "abilities": list(self.abilities), "cooldowns": dict(self.cooldowns),
            "history": self.history[-40:],
            "inventory": self.inventory.to_dicts(),
            "equipment": self.equipment.to_dicts(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Familiar":
        fam = cls(data.get("class_key", "loup"), data.get("name", ""),
                  int(data.get("level", 1) or 1))
        fam.xp = int(data.get("xp", 0) or 0)
        fam.max_hp = max(1, int(data.get("max_hp", fam.max_hp) or fam.max_hp))
        fam.hp = max(0, min(fam.max_hp, int(data.get("hp", fam.max_hp) or 0)))
        fam.atk = int(data.get("atk", fam.atk) or fam.atk)
        fam.defense = int(data.get("defense", fam.defense) or fam.defense)
        fam.speed = int(data.get("speed", fam.speed) or fam.speed)
        fam.max_mana = int(data.get("max_mana", fam.max_mana) or 0)
        fam.mana = int(data.get("mana", fam.max_mana) or 0)
        fam.order = data.get("order", "suivre") if data.get("order") in ORDERS else "suivre"
        fam.kills = int(data.get("kills", 0) or 0)
        fam.loot_taken = int(data.get("loot_taken", 0) or 0)
        fam.abilities = list(data.get("abilities") or [fam.cdef["ability"]])
        fam.cooldowns = {str(k): int(v) for k, v in (data.get("cooldowns") or {}).items()}
        fam.history = [str(h) for h in (data.get("history") or [])][-40:]
        fam.inventory = Inventory.from_dicts(data.get("inventory") or [], "familiar",
                                             fam.inventory.capacity)
        fam.equipment = Equipment(owner="familiar")
        fam.equipment.load(data.get("equipment") or {})
        fam.alive = fam.hp > 0
        return fam


def default_familiar(class_key: str = "loup") -> Familiar:
    """Familier de départ, avec un équipement commun adapté."""
    fam = Familiar(class_key)
    if class_key == "arcaniste":
        start = item_db.make_weapon("baton", 0)
    elif class_key in ("golem", "chevalier"):
        start = item_db.make_weapon("epee_lourde" if class_key == "golem" else "epee_courte", 0)
    else:
        start = item_db.make_weapon("dague", 0)
    start.owner = "familiar"
    fam.inventory.add(start, force_owner=True)
    armor_key = "lourde" if class_key in ("golem", "chevalier") else "legere"
    armor = item_db.make_armor(armor_key, 0)
    armor.owner = "familiar"
    if fam.inventory.add(armor, force_owner=True).startswith("Tu ramasses"):
        fam.equip_best()
    fam.add_history("Équipement de départ récupéré.")
    return fam