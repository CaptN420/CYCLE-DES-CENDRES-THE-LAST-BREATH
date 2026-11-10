"""Gestion centralisée des objets : identifiants uniques, propriétaires, localisations.

Règle d'or : un objet existe à UN seul endroit. Toute entrée/sortie passe par
l'`ItemManager`, qui refuse un identifiant déjà connu et garde une pierre
tombale pour les objets détruits.
"""
from __future__ import annotations

from . import item_db, items, ui

INVENTORY_PLAYER = "INVENTORY_PLAYER"
INVENTORY_FAMILIAR = "INVENTORY_FAMILIAR"
GROUND = "GROUND"
EQUIPPED_PLAYER = "EQUIPPED_PLAYER"
EQUIPPED_FAMILIAR = "EQUIPPED_FAMILIAR"
STORAGE = "STORAGE"
DESTROYED = "DESTROYED"

LOCATIONS = {INVENTORY_PLAYER, INVENTORY_FAMILIAR, GROUND,
             EQUIPPED_PLAYER, EQUIPPED_FAMILIAR, STORAGE, DESTROYED}


class ItemManager:
    """Registre unique : item_id -> localisation. Anti-duplication."""

    def __init__(self) -> None:
        self.locations: dict[str, str] = {}
        self.owners: dict[str, str] = {}
        self.objects: dict[str, int] = {}      # item_id -> id(objet) : détecte les vrais doublons
        self.tombstones: set[str] = set()
        self.duplicates_repaired: list[str] = []

    def reset(self) -> None:
        self.locations.clear()
        self.owners.clear()
        self.objects.clear()
        self.tombstones.clear()
        self.duplicates_repaired.clear()

    # ------------------------------------------------------------ claims
    def claim(self, item: items.Item, owner: str, location: str) -> bool:
        """Réserve l'objet. Refusé s'il est détruit ou déjà placé ailleurs."""
        if item.item_id in self.tombstones:
            return False
        known_object = self.objects.get(item.item_id)
        if known_object is not None and known_object != id(item):
            # même identifiant, objet différent : c'est une copie, on la refuse
            self.duplicates_repaired.append(item.item_id)
            return False
        self.objects[item.item_id] = id(item)
        self.locations[item.item_id] = location
        self.owners[item.item_id] = owner
        item.owner = owner
        item.location = location
        return True

    def restore(self, item: items.Item, owner: str, location: str) -> bool:
        """Réenregistre un objet chargé depuis une sauvegarde (objet neuf, même id)."""
        if item.item_id in self.tombstones:
            return False
        self.objects[item.item_id] = id(item)
        self.locations[item.item_id] = location
        self.owners[item.item_id] = owner
        item.owner = owner
        item.location = location
        return True

    def release(self, item: items.Item, location: str = DESTROYED) -> None:
        self.locations[item.item_id] = location
        item.location = location
        if location == DESTROYED:
            self.tombstones.add(item.item_id)

    def destroy(self, item: items.Item) -> bool:
        if item.item_id in self.tombstones:
            return False
        self.release(item, DESTROYED)
        item.stack = 0
        return True

    def is_destroyed(self, item_id: str) -> bool:
        return item_id in self.tombstones

    def location_of(self, item: items.Item) -> str | None:
        return self.locations.get(item.item_id)

    # --------------------------------------------------------- validation
    def validate(self, containers: list) -> dict:
        """Détecte un identifiant présent deux fois et coupe les doublons.

        On ne détruit rien : la première occurrence garde l'objet, les
        suivantes sont retirées du conteneur (l'objet reste unique).
        """
        seen: dict[str, int] = {}
        report = {"duplicates": [], "destroyed_found": [], "repaired": 0}
        for label, container in containers:
            for item in list(container):
                if item.item_id in self.tombstones:
                    container.remove(item)
                    report["destroyed_found"].append(item.item_id)
                    continue
                first = seen.get(item.item_id)
                if first is not None and first != id(item):
                    container.remove(item)
                    report["duplicates"].append(item.item_id)
                    self.duplicates_repaired.append(item.item_id)
                    report["repaired"] += 1
                    continue
                seen[item.item_id] = id(item)
        return report


MANAGER = ItemManager()


class Inventory(list):
    """Sac d'un personnage : capacité, empilement, tri, propriétaire."""

    STACKABLE = ("potion", "scroll", "material", "gold", "fragment")

    def __init__(self, owner: str = "player", capacity: int = 20,
                 location: str | None = None, manager: ItemManager | None = None):
        super().__init__()
        self.owner = owner
        self.capacity = capacity
        self.location = location or (INVENTORY_PLAYER if owner == "player" else INVENTORY_FAMILIAR)
        self.manager = manager or MANAGER

    # ------------------------------------------------------------- ajout
    def add(self, item: items.Item, force_owner: bool = False) -> str:
        if self.manager.is_destroyed(item.item_id):
            return "Cet objet n'existe plus."
        if any(existing is item for existing in self):
            return "Cet objet est déjà dans ce sac."
        if item.owner not in ("player", "familiar", "none", ""):
            return "Objet invalide."
        owner = self.owner
        if item.owner not in (owner, "none", "") and not force_owner:
            return ("Cet objet appartient à ton familier." if owner == "player"
                    else "Cet objet appartient au joueur.")
        for existing in self:
            if (existing.key == item.key and item.kind in self.STACKABLE
                    and existing.item_id != item.item_id):
                existing.stack += item.stack
                self.manager.release(item, DESTROYED)   # l'objet fusionné n'existe plus
                return f"{existing.name} (x{existing.stack})."
        if len(self) >= self.capacity:
            return "Le sac est plein."
        if not self.manager.claim(item, owner, self.location):
            return "Objet déjà possédé ailleurs."
        super().append(item)
        return f"Tu ramasses : {item.name}."

    def append(self, item: items.Item) -> None:  # type: ignore[override]
        """Appel direct (ancien code) : on enregistre quand même l'objet."""
        if self.manager.location_of(item) is None:
            self.manager.claim(item, self.owner, self.location)
        super().append(item)

    def extend(self, other) -> None:  # type: ignore[override]
        for item in other:
            self.append(item)

    # ------------------------------------------------------------ retrait
    def remove(self, item: items.Item) -> None:  # type: ignore[override]
        if item in self:
            super().remove(item)
            if self.manager.location_of(item) == self.location:
                self.manager.release(item, STORAGE)

    def take_id(self, item_id: str) -> items.Item | None:
        for item in self:
            if item.item_id == item_id:
                self.remove(item)
                return item
        return None

    def remove_item(self, item: items.Item, count: int = 1) -> None:
        """Consomme une unité (empilement) puis retire l'objet s'il est épuisé."""
        if item not in self:
            return
        item.stack -= max(0, count)
        if item.stack <= 0:
            item.stack = 0
            self.remove(item)

    def take(self, item: items.Item) -> bool:
        if item in self:
            self.remove(item)
            return True
        return False

    # -------------------------------------------------------------- divers
    def sort_items(self) -> None:
        order = {"weapon": 0, "armor": 1, "accessory": 2, "potion": 3, "scroll": 4,
                 "material": 5, "quest": 6, "key": 7, "fragment": 8, "gold": 9}
        self.sort(key=lambda it: (order.get(it.kind, 9), -it.rarity, it.name))

    def count_free(self) -> int:
        return max(0, self.capacity - len(self))

    def categories(self) -> dict[str, list[items.Item]]:
        buckets: dict[str, list[items.Item]] = {}
        for item in self:
            label = {"weapon": "ARMES", "armor": "ARMURES", "accessory": "ACCESSOIRES",
                     "potion": "CONSOMMABLES", "scroll": "PARCHEMINS",
                     "material": "MATÉRIAUX", "quest": "QUÊTES", "key": "CLÉS",
                     "fragment": "FRAGMENTS", "gold": "OR"}.get(item.kind, "DIVERS")
            buckets.setdefault(label, []).append(item)
        return buckets

    def to_dicts(self) -> list[dict]:
        return [item.to_dict() for item in self]

    @classmethod
    def from_dicts(cls, data: list[dict], owner: str, capacity: int,
                   manager: ItemManager | None = None) -> "Inventory":
        inv = cls(owner=owner, capacity=capacity, manager=manager)
        for entry in data or []:
            item = items.Item.from_dict(entry)
            if item.owner in ("", "none"):
                item.owner = owner
            if not inv.manager.restore(item, owner, inv.location):
                continue
            list.append(inv, item)          # sans passer par la capacité
        return inv


class Equipment:
    """Emplacements d'équipement (9 cases), avec retour au sac de l'ancien objet."""

    SLOTS = ("weapon", "offhand", "head", "chest", "hands", "feet", "amulet", "ring1", "ring2")

    def __init__(self, owner: str = "player", manager: ItemManager | None = None):
        self.owner = owner
        self.manager = manager or MANAGER
        self.slots: dict[str, items.Item] = {}

    def get(self, slot: str) -> items.Item | None:
        return self.slots.get(slot)

    def stat(self, name: str) -> int:
        total = 0
        for item in self.slots.values():
            total += int(item.stats.get(name, 0))
            if name == "defense" and item.kind in ("armor", "accessory") and not item.stats:
                total += int(item.power)
        return total

    def equip(self, item: items.Item, inventory: Inventory) -> tuple[bool, str]:
        if item.slot not in self.SLOTS:
            return False, "On ne peut pas équiper cet objet."
        if item.item_id in self.manager.tombstones:
            return False, "Cet objet n'existe plus."
        accepted = inventory.take(item)
        if not accepted:
            return False, "L'objet n'est pas dans le sac."
        old = self.slots.get(item.slot)
        self.slots[item.slot] = item
        self.manager.claim(item, self.owner, (EQUIPPED_PLAYER if self.owner == "player"
                                              else EQUIPPED_FAMILIAR))
        if old is not None:
            inventory.add(old, force_owner=True)
        return True, f"{item.name} équipé ({item_db.SLOT_FR.get(item.slot, item.slot)})."

    def unequip(self, slot: str, inventory: Inventory) -> tuple[bool, str]:
        item = self.slots.pop(slot, None)
        if item is None:
            return False, "Emplacement vide."
        msg = inventory.add(item, force_owner=True)
        return True, msg

    def to_dicts(self) -> dict:
        return {slot: item.to_dict() for slot, item in self.slots.items()}

    def load(self, data: dict) -> None:
        self.slots.clear()
        for slot in self.SLOTS:
            entry = (data or {}).get(slot)
            if not entry:
                continue
            item = items.Item.from_dict(entry)
            if not self.manager.restore(item, self.owner,
                                        (EQUIPPED_PLAYER if self.owner == "player"
                                         else EQUIPPED_FAMILIAR)):
                continue
            item.slot = item.slot or slot
            self.slots[slot] = item


def destroy_item(item: items.Item, container) -> str:
    """Destruction définitive : retire de partout et pose une pierre tombale."""
    if container is not None and item in container:
        container.remove(item)
    MANAGER.destroy(item)
    return f"{item.name} est détruit. Il ne reviendra pas."


def item_line(item: items.Item, equipped: bool = False) -> str:
    """Ligne colorée avec la rareté (pour les menus)."""
    color = item_db.rarity_color(item.rarity) if item.rarity else item.color
    tag = " [équipé]" if equipped else ""
    return (ui.paint(item.glyph, color) + " " + ui.paint(item.label, color)
            + (ui.paint(tag, ui.GREEN) if tag else ""))