"""Butin : attribution par tueur, récompenses de boss séparées, garde anti-duplication."""
from __future__ import annotations

import random

from . import item_db, items


def roll_loot(monster, owner: str, depth: int, rng: random.Random,
              chance: float = 0.45, luck: float = 0.0) -> list[items.Item]:
    """Butin d'un monstre, attribué à SON tueur dès la génération."""
    if getattr(monster, "loot_generated", False):
        return []
    monster.loot_generated = True
    drops: list[items.Item] = []
    guaranteed = list(getattr(monster, "drops", []) or [])
    monster.drops = []
    for item in guaranteed:
        _stamp(item, owner)
        drops.append(item)
    if rng.random() < chance + luck:
        item = item_db.random_item(rng, depth)
        _stamp(item, owner)
        drops.append(item)
    if rng.random() < 0.10 + luck:
        mat = item_db.make_material(rng.choice(["fer", "cuir", "essence"]), rng.randint(1, 2))
        _stamp(mat, owner)
        drops.append(mat)
    return drops


def boss_loot(owner: str, depth: int, rng: random.Random, class_key: str = "loup",
              count: int = 1) -> list[items.Item]:
    """Récompense de boss : le familier a la sienne, le joueur aussi."""
    out: list[items.Item] = []
    for _ in range(count):
        rarity = rng.choices([2, 3, 4], weights=[55, 33, 12], k=1)[0]
        if owner == "familiar":
            kind = "weapon" if rng.random() < 0.5 else ("armor" if rng.random() < 0.6 else "accessory")
            item = item_db.random_item(rng, depth, rarity=rarity, kind=kind)
            while item.stats.get("dmg", 0) == 0 and item.kind == "weapon" and rng.random() < 0.5:
                item = item_db.random_item(rng, depth, rarity=rarity, kind="weapon")
        else:
            item = item_db.random_item(rng, depth, rarity=rarity)
        _stamp(item, owner)
        out.append(item)
    mat = item_db.make_material("fragment" if owner == "familiar" else "cristal", 1)
    _stamp(mat, owner)
    out.append(mat)
    return out


def evolution_material(owner: str = "familiar") -> items.Item:
    item = item_db.make_material("essence", 1)
    _stamp(item, owner)
    return item


def _stamp(item: items.Item, owner: str) -> items.Item:
    item.owner = owner
    item.location = "GROUND"
    return item