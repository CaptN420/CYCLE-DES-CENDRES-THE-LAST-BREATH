"""Objets, armes, armures, parchemins et butin."""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field

from . import ui


def new_item_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class Item:
    key: str
    name: str
    glyph: str
    color: int
    kind: str  # weapon | armor | accessory | potion | scroll | material | gold | fragment | quest | key
    power: int = 0
    desc: str = ""
    stack: int = 1
    # --- identité et propriété (système anti-duplication) --------------
    item_id: str = field(default_factory=new_item_id)
    owner: str = "player"          # player | familiar | none
    location: str = "INVENTORY_PLAYER"
    slot: str = ""                 # weapon | offhand | head | chest | hands | feet | amulet | ring1 | ring2
    rarity: int = 0                # 0 commun .. 4 légendaire
    stats: dict = field(default_factory=dict)   # dmg, def, speed, crit, mana, regen, resist, detect
    effects: tuple = ()
    base_key: str = ""             # clé de base dans item_db ("" pour les objets historiques)

    @property
    def label(self) -> str:
        if self.stack > 1:
            return f"{self.name} x{self.stack}"
        return self.name

    def copy(self, count: int = 1) -> "Item":
        """Copie *nouvelle* : identifiant neuf, l'original n'est pas partagé."""
        return Item(self.key, self.name, self.glyph, self.color, self.kind,
                    self.power, self.desc, count)

    def to_dict(self) -> dict:
        return {
            "key": self.key, "name": self.name, "glyph": self.glyph,
            "color": self.color, "kind": self.kind, "power": self.power,
            "desc": self.desc, "stack": self.stack, "item_id": self.item_id,
            "owner": self.owner, "location": self.location, "slot": self.slot,
            "rarity": self.rarity, "stats": dict(self.stats),
            "effects": list(self.effects), "base_key": self.base_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        item = cls(
            str(data.get("key", "?"))[:40], str(data.get("name", "objet"))[:60],
            str(data.get("glyph", "?"))[:2], int(data.get("color", ui.WHITE) or ui.WHITE),
            str(data.get("kind", "misc")), int(data.get("power", 0) or 0),
            str(data.get("desc", "")), max(1, int(data.get("stack", 1) or 1)),
        )
        item.item_id = str(data.get("item_id") or new_item_id())
        item.owner = str(data.get("owner", "player"))
        item.location = str(data.get("location", "INVENTORY_PLAYER"))
        item.slot = str(data.get("slot", ""))
        item.rarity = int(data.get("rarity", 0) or 0)
        stats = data.get("stats") or {}
        item.stats = {str(k): int(v) for k, v in stats.items() if isinstance(v, (int, float))}
        item.effects = tuple(str(e) for e in (data.get("effects") or []))
        item.base_key = str(data.get("base_key", ""))
        return item


WEAPONS = [
    ("dague", "Dague rouillée", ")", ui.MIDGREY, 2, "Officielle, émoussée, mais loyale."),
    ("epee_courte", "Épée courte", ")", ui.BONE, 4, "L'acier des gardes morts."),
    ("hache", "Hache naine", ")", ui.ORANGE, 6, "Lourde. Elle a fendu des crânes et des portes."),
    ("lame", "Lame des forges", ")", ui.GOLD, 9, "Encore tiède après mille ans."),
    ("fauche_noir", "Fauchenoir", ")", ui.PURPLE, 12, "Elle coupe aussi les souvenirs."),
    ("souffle", "Dernier Souffle", ")", ui.WHITE, 15, "L'épée qui attendait un porteur."),
    # Nouvelles armes
    ("arc", "Arc du rôdeur", "'", ui.GREEN, 5, "Tendu depuis mille ans. Il se souvient de ta main."),
    ("lame_gel", "Lame de gel", ")", ui.CYAN, 7, "Froide comme la pierre où tu t'es endormi."),
    ("marteau", "Marteau du forgeron", ")", ui.BRIGHTRED, 10, "Il pèse deux fois plus que ce qu'il devrait."),
    ("poignard_sorcier", "Poignard de cendre", ")", ui.PURPLE, 8, "Brûle sans chauffer. Tranche sans bruit."),
    ("hache_guerriere", "Hache de guerre", ")", ui.RED, 11, "Rouillée mais équilibrée. Elle a connu mieux."),
]

ARMORS = [
    ("chiffons", "Chiffons", "[", ui.DARKGREY, 0, "Tu as connu mieux. Ou pas."),
    ("cuir", "Armure de cuir usé", "[", ui.BROWN, 1, "Craque à chaque pas."),
    ("cotte", "Cotte de mailles", "[", ui.MIDGREY, 2, "Froide, lourde, rassurante."),
    ("plastron", "Plastron nain", "[", ui.CYAN, 3, "Gravé d'un nom effacé : le tien ?"),
    ("armure_neant", "Armure du Néant", "[", ui.PURPLE, 5, "Elle ne protège pas. Elle absorbe."),
    # Nouvelles armures
    ("cotte_rondeur", "Cotte du rôdeur", "[", ui.GREEN, 2, "Légère. Elle te permet de courir encore."),
    ("plate", "Plaque du forgeron", "[", ui.ORANGE, 4, "Gravée de runes qui ne marchent plus."),
]

POTIONS = [
    ("soin", "Potion de soin", "!", ui.BRIGHTRED, 10, "Une chaleur rouge dans la gorge.", "heal"),
    ("antidote", "Potion d'antidote", "!", ui.GREEN, 0, "Goût de cendre et de menthe.", "cure"),
    ("vigueur", "Élixir de vigueur", "!", ui.YELLOW, 4, "Ton corps se souvient d'être plus solide.", "vigor"),
    ("sagesse", "Liquide de sagesse", "!", ui.BLUE, 0, "Tu vois les murs respirer. (-2 PV max)", "wisdom"),
    ("force_brutale", "Élixir de force brute", "!", ui.RED, 6, "Tes muscles hurlent. (+6 PV max)", "brute"),
]

SCROLLS = [
    ("teleport", "Parchemin de téléportation", "?", ui.CYAN, 0, "L'encre tremble sur le papier.", "teleport"),
    ("carto", "Parchemin de cartographie", "?", ui.BLUE, 0, "Les murs s'impriment derrière tes paupières.", "map"),
    ("flammes", "Parchemin de flammes", "?", ui.ORANGE, 14, "Une écriture qui brûle les doigts.", "fire"),
    ("froid", "Parchemin de froid", "?", ui.CYAN, 12, "Un vent glacial sort du rouleau.", "frost"),
    ("sommeil", "Parchemin de sommeil", "?", ui.PURPLE, 0, "Les lettres dansent avant de s'effacer.", "sleep"),
]


def make_weapon(depth: int, rng: random.Random) -> Item:
    best = min(3 + depth, len(WEAPONS))
    weights = [max(1, 10 - i * 2) for i in range(best)]
    idx = rng.choices(range(best), weights=weights, k=1)[0]
    key, name, glyph, color, power, desc = WEAPONS[idx]
    return Item(f"w_{key}", name, glyph, color, "weapon", power, desc)


def make_armor(depth: int, rng: random.Random) -> Item:
    best = min(2 + depth, len(ARMORS))
    weights = [max(1, 10 - i * 2) for i in range(best)]
    idx = rng.choices(range(best), weights=weights, k=1)[0]
    key, name, glyph, color, power, desc = ARMORS[idx]
    return Item(f"a_{key}", name, glyph, color, "armor", power, desc)


def make_potion(rng: random.Random) -> Item:
    key, name, glyph, color, power, desc, _effect = rng.choice(POTIONS)
    return Item(f"p_{key}", name, glyph, color, "potion", power, desc)


def make_scroll(rng: random.Random) -> Item:
    key, name, glyph, color, power, desc, _effect = rng.choice(SCROLLS)
    return Item(f"s_{key}", name, glyph, color, "scroll", power, desc)


def make_gold(amount: int) -> Item:
    return Item("gold", "pièces d'or", "$", ui.GOLD, "gold", amount, "Brille dans la poussière.")


def make_fragment() -> Item:
    return Item("fragment", "Fragment divin", "*", ui.YELLOW, "fragment", 1,
                "Un éclat d'âme divine. Il est tiède et il bat.")


def make_black_key() -> Item:
    return Item("cle_noire", "Vieille clé noire", "/", ui.PURPLE, "key", 0,
                "Elle n'ouvre aucune porte. Elle te désigne.")


def make_heart() -> Item:
    return Item("coeur", "Cœur de squelette", "&", ui.RED, "quest", 0,
                "Il bat encore, très faiblement. Il t'appartient peut-être.")


def make_loot(depth: int, rng: random.Random) -> Item:
    roll = rng.random()
    if roll < 0.30:
        return make_weapon(depth, rng)
    if roll < 0.55:
        return make_armor(depth, rng)
    if roll < 0.75:
        return make_potion(rng)
    if roll < 0.90:
        return make_scroll(rng)
    return make_gold(rng.randint(4, 10 + depth * 6))


def make_quest_heart() -> Item:
    """Cœur de squelette — drop rare des squelettes, item quest."""
    return Item("coeur", "Cœur de squelette", "&", ui.RED, "quest", 0,
                "Il bat encore, très faiblement. Il t'appartient peut-être.")


def make_activated_key() -> Item:
    """Clé noire activée — apparaît à 7 fragments + insight 5."""
    return Item("cle_activee", "Clé noire illuminée", "/", ui.YELLOW, "key", 0,
                "Elle brille maintenant. Elle montre le chemin.")


# ---------------------------------------------------------------- Chapitre II
CH2_WEAPONS = [
    ("lame_ames", "Lame des Âmes", ")", ui.PURPLE, 14, "Forgée avec un souvenir qui n'est pas le tien."),
    ("crochet", "Crochet de la Nécropole", ")", ui.BONE, 17, "Il a servi à compter les morts."),
    ("marteau", "Marteau du Premier Monde", ")", ui.ORANGE, 20, "Il a façonné les premiers visages."),
    ("fil", "Fil du Silence", ")", ui.WHITE, 24, "Il coupe ce qui n'a pas de nom."),
]

CH2_ARMORS = [
    ("manteau", "Manteau de cendre", "[", ui.MIDGREY, 4, "Il ne protège pas du froid, seulement des regards."),
    ("plastron2", "Plastron de roi mort", "[", ui.BONE, 6, "Il a été porté par mille rois, une fois chacun."),
    ("cuirasse", "Cuirasse de givre", "[", ui.CYAN, 8, "Froide, solide, un peu vivante."),
    ("peau", "Peau du Néant", "[", ui.PURPLE, 10, "On ne sait plus où finit l'armure, où commence le corps."),
]


def make_ch2_weapon(tier: int = 0) -> Item:
    key, name, glyph, color, power, desc = CH2_WEAPONS[max(0, min(len(CH2_WEAPONS) - 1, tier))]
    return Item(f"c2_{key}", name, glyph, color, "weapon", power, desc)


def make_ch2_armor(tier: int = 0) -> Item:
    key, name, glyph, color, power, desc = CH2_ARMORS[max(0, min(len(CH2_ARMORS) - 1, tier))]
    return Item(f"c2_{key}", name, glyph, color, "armor", power, desc)


def random_vendor_stock(depth: int, rng: random.Random) -> Item:
    """Objet proposé par le marchand maudit (prix calculé à part)."""
    if rng.random() < 0.45:
        return make_weapon(depth + 1, rng)
    if rng.random() < 0.5:
        return make_armor(depth + 1, rng)
    return rng.choice([make_potion(rng), make_scroll(rng)])
