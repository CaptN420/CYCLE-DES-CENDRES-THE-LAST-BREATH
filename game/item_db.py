"""Base d'objets : 40 objets utiles, 5 raretés, statistiques et affinités."""
from __future__ import annotations

import random  # noqa: F401

from . import items, ui

RARITIES = [
    ("Commun", ui.MIDGREY, 1.00),
    ("Peu commun", ui.GREEN, 1.18),
    ("Rare", ui.CYAN, 1.40),
    ("Épique", ui.PURPLE, 1.70),
    ("Légendaire", ui.GOLD, 2.10),
]

RARITY_WEIGHTS = [
    (0, 58), (1, 26), (2, 11), (3, 4), (4, 1),   # par défaut
]


def rarity_name(rarity: int) -> str:
    return RARITIES[max(0, min(4, rarity))][0]


def rarity_color(rarity: int) -> int:
    return RARITIES[max(0, min(4, rarity))][1]


# ---------------------------------------------------------------- armes
# dmg, speed (plus haut = plus rapide), crit (%)
WEAPONS = {
    "epee_courte": dict(name="Épée courte", glyph=")", color=ui.BONE, dmg=5, speed=10, crit=5,
                        desc="Équilibrée. Elle pardonne les erreurs.", classes=("chevalier", "loup")),
    "epee_lourde": dict(name="Épée lourde", glyph=")", color=ui.MIDGREY, dmg=9, speed=6, crit=3,
                        desc="Deux mains, une seule idée.", classes=("chevalier", "golem")),
    "dague": dict(name="Dague", glyph=")", color=ui.CYAN, dmg=3, speed=15, crit=14,
                  desc="Rapide. Elle cherche la gorge.", classes=("loup", "corbeau")),
    "hache": dict(name="Hache", glyph=")", color=ui.ORANGE, dmg=8, speed=8, crit=6,
                  desc="Fend les armures et les certitudes.", classes=("golem", "loup")),
    "arc": dict(name="Arc", glyph="'", color=ui.GREEN, dmg=6, speed=11, crit=9,
                desc="Tire avant que l'autre ne décide.", classes=("corbeau", "arcaniste"), ranged=True),
    "baton": dict(name="Bâton arcanique", glyph="/", color=ui.PURPLE, dmg=4, speed=9, crit=4,
                  desc="Il se souvient des sorts.", classes=("arcaniste",), mana=8),
    "lance": dict(name="Lance", glyph="/", color=ui.BROWN, dmg=7, speed=9, crit=7,
                  desc="Garde l'ennemi à distance d'un bras.", classes=("chevalier", "golem"), reach=True),
}

# ---------------------------------------------------------------- armures
ARMORS = {
    "legere": dict(name="Armure légère", glyph="[", color=ui.GREEN, defense=3, speed=2,
                   desc="On bouge encore.", classes=("loup", "corbeau")),
    "intermediaire": dict(name="Armure intermédiaire", glyph="[", color=ui.MIDGREY, defense=5, speed=0,
                          desc="Le compromis des vivants.", classes=("chevalier", "loup")),
    "lourde": dict(name="Armure lourde", glyph="[", color=ui.CYAN, defense=8, speed=-2,
                   desc="Une porte portée sur soi.", classes=("golem", "chevalier")),
    "magique": dict(name="Armure magique", glyph="[", color=ui.PURPLE, defense=5, resist=4,
                    desc="Les éléments hésitent.", classes=("arcaniste",)),
    "maudite": dict(name="Armure maudite", glyph="[", color=ui.RED, defense=10, speed=-1, curse=True,
                    desc="Puissante. Elle réclame quelque chose.", classes=("golem",)),
}

ACCESSORIES = {
    "anneau_regen": dict(name="Anneau de régénération", glyph="o", color=ui.GREEN, slot="ring1",
                         stats=dict(regen=2, defense=1), desc="La chair se souvient de guérir."),
    "anneau_resist": dict(name="Anneau de résistance", glyph="o", color=ui.CYAN, slot="ring2",
                          stats=dict(resist=4, defense=1), desc="Le feu s'éteint avant."),
    "amulette_protection": dict(name="Amulette de protection", glyph='"', color=ui.GOLD, slot="amulet",
                                stats=dict(defense=3, resist=2), desc="Un dieu y a laissé un souffle."),
    "amulette_detection": dict(name="Amulette de détection", glyph='"', color=ui.PURPLE, slot="amulet",
                               stats=dict(detect=6, speed=1), desc="Les pièges deviennent bavards."),
    "bottes_vitesse": dict(name="Bottes de vitesse", glyph="^", color=ui.YELLOW, slot="feet",
                           stats=dict(speed=4, defense=1), desc="Le sol défile trop vite."),
    "gants_puissance": dict(name="Gants de puissance", glyph="=", color=ui.ORANGE, slot="hands",
                            stats=dict(dmg=3, crit=4), desc="La prise ne lâche plus."),
    "casque_garde": dict(name="Casque du garde", glyph="^", color=ui.MIDGREY, slot="head",
                         stats=dict(defense=2), desc="Il a arrêté un coup de hache."),
    "bouclier": dict(name="Bouclier ébréché", glyph=")", color=ui.BROWN, slot="offhand",
                     stats=dict(defense=4, speed=-1), desc="Trois flèches, trois souvenirs."),
}

# ------------------------------------------------------------ consommables
CONSUMABLES = {
    "soin": dict(name="Potion de soin", power=14, color=ui.BRIGHTRED, effect="heal",
                 desc="Une chaleur rouge dans la gorge."),
    "grande_soin": dict(name="Grande potion de soin", power=32, color=ui.RED, effect="heal",
                        desc="On sent ses os se remettre droit."),
    "mana": dict(name="Potion de mana", power=20, color=ui.BLUE, effect="mana",
                 desc="L'air devient lisible."),
    "vigueur": dict(name="Potion de vigueur", power=6, color=ui.YELLOW, effect="vigor", turns=12,
                    desc="Les muscles se souviennent d'être sûrs d'eux."),
    "resistance": dict(name="Potion de résistance", power=5, color=ui.CYAN, effect="resist", turns=12,
                       desc="Le monde mord moins fort."),
    "antidote": dict(name="Antidote", power=0, color=ui.GREEN, effect="cure",
                     desc="Goût de cendre et de menthe."),
    "vitesse": dict(name="Potion de vitesse", power=4, color=ui.YELLOW, effect="haste", turns=10,
                    desc="Les secondes s'étirent."),
    "regeneration": dict(name="Élixir de régénération", power=3, color=ui.GREEN, effect="regen", turns=10,
                         desc="La douleur se referme toute seule."),
    "bombe_feu": dict(name="Bombe incendiaire", power=12, color=ui.ORANGE, effect="bomb",
                      desc="Zone : tout ce qui est proche brûle."),
    "bombe_fumee": dict(name="Bombe de fumée", power=0, color=ui.DARKGREY, effect="smoke",
                        desc="On te perd de vue. C'est déjà beaucoup."),
}

MATERIALS = {
    "fer": dict(name="Fer ancien", color=ui.MIDGREY,
                desc="Améliore les armes (+1 dégâts par pièce)."),
    "cuir": dict(name="Cuir renforcé", color=ui.BROWN,
                 desc="Améliore les armures (+1 défense par pièce)."),
    "cristal": dict(name="Cristal arcanique", color=ui.CYAN,
                    desc="Améliore les objets magiques (+mana)."),
    "essence": dict(name="Essence spectrale", color=ui.PURPLE,
                    desc="Façonne les accessoires."),
    "fragment": dict(name="Fragment divin", color=ui.YELLOW,
                     desc="Améliore un objet jusqu'au légendaire."),
}

# Pondérations d'évaluation par classe : ce que vaut chaque statistique.
CLASS_WEIGHTS = {
    "loup": {"dmg": 1.3, "speed": 1.15, "crit": 1.5, "defense": 0.5, "hp": 0.3, "resist": 0.4,
             "regen": 0.9, "mana": 0.0, "detect": 0.2},
    "golem": {"dmg": 1.4, "speed": 0.3, "crit": 0.3, "defense": 2.4, "hp": 0.6, "resist": 0.8,
              "regen": 0.6, "mana": 0.0, "detect": 0.0},
    "arcaniste": {"dmg": 0.7, "speed": 0.8, "crit": 0.8, "defense": 0.5, "hp": 0.2, "resist": 1.2,
                  "regen": 0.6, "mana": 2.2, "detect": 0.6},
    "corbeau": {"dmg": 0.9, "speed": 1.5, "crit": 1.4, "defense": 0.4, "hp": 0.2, "resist": 0.5,
                "regen": 0.5, "mana": 0.0, "detect": 1.8},
    "chevalier": {"dmg": 1.1, "speed": 0.8, "crit": 0.9, "defense": 1.8, "hp": 0.4, "resist": 1.0,
                  "regen": 0.7, "mana": 0.0, "detect": 0.3},
}

SLOT_FR = {
    "weapon": "Arme", "offhand": "Secondaire", "head": "Casque", "chest": "Armure",
    "hands": "Gants", "feet": "Bottes", "amulet": "Amulette",
    "ring1": "Anneau 1", "ring2": "Anneau 2",
}


def _scale(value: float, rarity: int) -> int:
    mult = RARITIES[max(0, min(4, rarity))][2]
    return max(0, int(round(value * mult)))


def item_score(item: items.Item, class_key: str = "loup") -> float:
    """Valeur réelle d'un objet pour une classe (pas seulement les dégâts)."""
    weights = CLASS_WEIGHTS.get(class_key, CLASS_WEIGHTS["loup"])
    stats = dict(item.stats)
    if item.kind == "weapon":
        stats.setdefault("dmg", item.power)
    elif item.kind in ("armor", "accessory"):
        stats.setdefault("defense", item.power)
    score = 0.0
    for name, value in stats.items():
        score += float(value) * weights.get(name, 0.3)
    score += item.rarity * 2.2
    return round(score, 2)


def _base_item(base_key: str, kind: str, rarity: int, prefix: str) -> items.Item:
    table = {"weapon": WEAPONS, "armor": ARMORS, "accessory": ACCESSORIES,
             "consumable": CONSUMABLES, "material": MATERIALS}[kind]
    base = table[base_key]
    name = base["name"]
    if rarity >= 4:
        name = name + " du Néant"
    elif rarity == 3:
        name = name + " spectrale"
    elif rarity == 2:
        name = name + " ancienne"
    color = rarity_color(rarity) if rarity >= 2 else base.get("color", ui.BONE)
    item = items.Item(
        key=f"{prefix}_{base_key}_{rarity}", name=name, glyph=base.get("glyph", "?"),
        color=color, kind={"consumable": "potion", "material": "material"}.get(kind, kind),
        power=0, desc=base.get("desc", ""), base_key=base_key,
    )
    item.rarity = rarity
    if kind == "weapon":
        dmg = _scale(base["dmg"], rarity)
        item.stats = {"dmg": dmg, "speed": base["speed"], "crit": base["crit"] + rarity}
        item.power = dmg
        item.slot = "weapon"
        for flag in ("ranged", "reach"):
            if base.get(flag):
                item.effects = item.effects + (flag,)
        if base.get("mana"):
            item.stats["mana"] = _scale(base["mana"], rarity)
    elif kind == "armor":
        defense = _scale(base["defense"], rarity)
        item.stats = {"defense": defense, "speed": base.get("speed", 0)}
        if base.get("resist"):
            item.stats["resist"] = _scale(base["resist"], rarity)
        item.power = defense
        item.slot = "chest"
        if base.get("curse"):
            item.effects = item.effects + ("curse",)
    elif kind == "accessory":
        item.stats = {k: _scale(v, rarity) for k, v in base["stats"].items()}
        item.power = item.stats.get("defense", 0)
        item.slot = base["slot"]
    elif kind == "consumable":
        item.power = base["power"]
        item.effects = (base["effect"],)
        item.stack = 1
    elif kind == "material":
        item.power = 1
        item.effects = ("material",)
    return item


def roll_rarity(rng: random.Random, depth: int, bonus: float = 0.0) -> int:
    base = [(0, 58), (1, 26), (2, 11 + depth), (3, 4 + depth // 2), (4, 1 + depth // 4)]
    weights = [(r, max(1, w + (bonus * 10 if r >= 2 else 0))) for r, w in base]
    total = sum(w for _r, w in weights)
    pick = rng.uniform(0, total)
    upto = 0.0
    for rarity, weight in weights:
        upto += weight
        if pick <= upto:
            return rarity
    return 0


def random_item(rng: random.Random, depth: int = 1, rarity: int | None = None,
                kind: str | None = None) -> items.Item:
    """Fabrique un objet cohérent avec la profondeur."""
    if rarity is None:
        rarity = roll_rarity(rng, depth)
    kinds = [kind] if kind else ["weapon", "armor", "accessory", "consumable", "material"]
    weights = [30, 22, 16, 24, 8] if not kind else [1]
    if kind == "weapon":
        pool = ["epee_courte", "epee_lourde", "dague", "hache", "arc", "baton", "lance"]
    elif kind == "armor":
        pool = ["legere", "intermediaire", "lourde", "magique", "maudite"]
    elif kind == "accessory":
        pool = list(ACCESSORIES)
    elif kind == "consumable":
        pool = list(CONSUMABLES)
    elif kind == "material":
        pool = list(MATERIALS)
    else:
        chosen = rng.choices(kinds, weights=weights, k=1)[0]
        return random_item(rng, depth, rarity, chosen)
    base_key = rng.choice(pool)
    prefix = {"weapon": "w", "armor": "a", "accessory": "acc"}.get(kind, "c")
    return _base_item(base_key, kind, rarity, prefix)


def consumable(effect: str, rng: random.Random | None = None) -> items.Item:
    """Objet consommable précis (soin, antidote, bombe...)."""
    for key, base in CONSUMABLES.items():
        if base["effect"] == effect:
            return _base_item(key, "consumable", 0, "c")
    raise KeyError(effect)


def make_weapon(base_key: str, rarity: int = 0) -> items.Item:
    return _base_item(base_key, "weapon", rarity, "w")


def make_armor(base_key: str, rarity: int = 0) -> items.Item:
    return _base_item(base_key, "armor", rarity, "a")


def make_accessory(base_key: str, rarity: int = 0) -> items.Item:
    return _base_item(base_key, "accessory", rarity, "acc")


def make_material(base_key: str, count: int = 1) -> items.Item:
    item = _base_item(base_key, "material", 0, "mat")
    item.stack = max(1, count)
    return item


def compare_lines(new: items.Item, old: items.Item | None, class_key: str) -> list[tuple[str, str]]:
    """Lignes de comparaison lisibles (stat, "+3" / "-2" / "=")."""
    rows: list[tuple[str, str]] = []
    keys = set(new.stats) | set((old.stats if old else {}))
    for stat in ("dmg", "defense", "speed", "crit", "mana", "regen", "resist", "detect"):
        if stat not in keys:
            continue
        a = int(new.stats.get(stat, 0))
        b = int(old.stats.get(stat, 0)) if old else 0
        diff = a - b
        sign = "=" if diff == 0 else (f"+{diff}" if diff > 0 else str(diff))
        rows.append((stat.capitalize(), sign))
    rows.append(("Valeur", f"{item_score(new, class_key):.1f}"))
    return rows