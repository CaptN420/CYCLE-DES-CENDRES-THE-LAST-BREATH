"""Mémoire persistante du donjon : le jeu se souvient de tes morts."""
from __future__ import annotations

import copy
import json
import os
import time
from dataclasses import dataclass, field

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "save")
SAVE_FILE = os.path.join(SAVE_DIR, "memoire.json")

DEFAULT = {
    "cycle": 1,
    "insight": 0,
    "deaths": [],
    "inscriptions": [],   # textes lus lors des cycles précédents
    "endings": [],        # fins atteintes
    "fragments_max": 0,
    "runs": 0,
    "best_depth": 1,
    # --- Chapitre II : progression persistante -------------------------
    "chapter2": {
        "deaths": 0,
        "death_log": [],
        "souvenirs": 0,
        "knowledge": 0,
        "npcs": [],
        "endings": [],
        "runs": 0,
        "kael_ally": False,
        "aureth_deal": False,
        "last_region": "",
        "legacy_grants": [],
        "ch3_teaser": False,
    },
    # --- Chapitre III : l'Intervalle ------------------------------------
    "chapter3": {
        "deaths": 0,
        "death_log": [],
        "memories": [],
        "pages": 0,
        "endings": [],
        "runs": 0,
        "varken_spared": False,
        "elia_helped": False,
        "creator_refused": False,
        "secret_room": False,
        "best_pages": 0,
        "ch4_teaser": False,
    },
}


@dataclass
class Death:
    floor: int
    cause: str
    cycle: int
    weapon: str = ""
    armor: str = ""
    kills: int = 0
    gold: int = 0
    fragments: int = 0
    ts: float = 0.0


class Memory:
    """Petit fichier JSON à côté du jeu (pas de compte, pas de réseau)."""

    def __init__(self, path: str = SAVE_FILE):
        self.path = path
        self.data = copy.deepcopy(DEFAULT)
        self.data["deaths"] = []
        self.data["inscriptions"] = []
        self.data["endings"] = []
        self.load()

    # ------------------------------------------------------------------ io
    def load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError):
            return
        if not isinstance(raw, dict):
            return
        for key, value in raw.items():
            if key not in DEFAULT:
                self.data[key] = value          # clés futures (ex : familier), jamais perdues
        for key, default in DEFAULT.items():
            value = raw.get(key, default)
            if isinstance(default, list) and not isinstance(value, list):
                value = list(default)
            if isinstance(default, int) and not isinstance(value, int):
                value = default
            if isinstance(default, dict):
                merged = dict(default)
                if isinstance(value, dict):
                    merged.update(value)
                value = merged
            self.data[key] = value

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except OSError:
            pass

    # ------------------------------------------------------------ accessors
    @property
    def cycle(self) -> int:
        return int(self.data.get("cycle", 1))

    @property
    def insight(self) -> int:
        return int(self.data.get("insight", 0))

    @property
    def deaths(self) -> list[dict]:
        return self.data.setdefault("deaths", [])

    @property
    def inscriptions(self) -> list[str]:
        return self.data.setdefault("inscriptions", [])

    @property
    def endings(self) -> list[str]:
        return self.data.setdefault("endings", [])

    @property
    def best_depth(self) -> int:
        return int(self.data.get("best_depth", 1))

    # ------------------------------------------------------- chapitre II
    @property
    def ch2(self) -> dict:
        data = self.data.setdefault("chapter2", {})
        if not isinstance(data, dict):
            data = {}
            self.data["chapter2"] = data
        for key, default in DEFAULT["chapter2"].items():
            data.setdefault(key, default)
        return data

    def add_ch2_knowledge(self, amount: int = 1) -> int:
        ch2 = self.ch2
        ch2["knowledge"] = min(9, int(ch2.get("knowledge", 0)) + amount)
        self.save()
        return ch2["knowledge"]

    def add_ch2_souvenirs(self, amount: int) -> int:
        ch2 = self.ch2
        ch2["souvenirs"] = max(0, int(ch2.get("souvenirs", 0)) + amount)
        self.save()
        return ch2["souvenirs"]

    def meet_npc(self, key: str) -> bool:
        ch2 = self.ch2
        if key in ch2["npcs"]:
            return False
        ch2["npcs"].append(key)
        self.save()
        return True

    def record_ch2_death(self, region: str, cause: str, player) -> dict:
        ch2 = self.ch2
        record = {
            "region": str(region),
            "cause": str(cause),
            "weapon": player.weapon.name if player.weapon else "mains nues",
            "armor": player.armor.name if player.armor else "aucune",
            "level": int(player.level),
            "fragments": int(player.fragments),
            "ts": time.time(),
        }
        ch2["deaths"] = int(ch2.get("deaths", 0)) + 1
        ch2["death_log"].append(record)
        ch2["death_log"] = ch2["death_log"][-30:]
        ch2["runs"] = int(ch2.get("runs", 0)) + 1
        ch2["last_region"] = region
        self.save()
        return record

    def record_ch2_ending(self, key: str) -> None:
        ch2 = self.ch2
        if key not in ch2["endings"]:
            ch2["endings"].append(key)
        self.save()

    # ------------------------------------------------------ chapitre III
    @property
    def ch3(self) -> dict:
        data = self.data.setdefault("chapter3", {})
        if not isinstance(data, dict):
            data = {}
            self.data["chapter3"] = data
        for key, default in DEFAULT["chapter3"].items():
            data.setdefault(key, default)
        return data

    def has_ch3_memory(self, key: str) -> bool:
        return key in self.ch3["memories"]

    def add_ch3_memory(self, key: str) -> bool:
        ch3 = self.ch3
        if key in ch3["memories"]:
            return False
        ch3["memories"].append(key)
        self.save()
        return True

    def remove_ch3_memory(self, key: str) -> bool:
        ch3 = self.ch3
        if key in ch3["memories"]:
            ch3["memories"].remove(key)
            self.save()
            return True
        return False

    def record_ch3_death(self, territory: str, cause: str, player) -> dict:
        ch3 = self.ch3
        record = {
            "territory": str(territory),
            "cause": str(cause),
            "weapon": player.weapon.name if player.weapon else "mains nues",
            "level": int(player.level),
            "pages": int(ch3.get("pages", 0)),
            "ts": time.time(),
        }
        ch3["deaths"] = int(ch3.get("deaths", 0)) + 1
        ch3["death_log"].append(record)
        ch3["death_log"] = ch3["death_log"][-30:]
        ch3["runs"] = int(ch3.get("runs", 0)) + 1
        self.save()
        return record

    def record_ch3_ending(self, key: str) -> None:
        ch3 = self.ch3
        if key not in ch3["endings"]:
            ch3["endings"].append(key)
        self.save()

    def has_read(self, text: str) -> bool:
        return text in self.inscriptions

    def add_inscription(self, text: str) -> bool:
        """Retourne True si c'est un nouveau souvenir (gain d'intuition)."""
        if text in self.inscriptions:
            return False
        self.inscriptions.append(text)
        self.data["insight"] = min(9, int(self.data.get("insight", 0)) + 1)
        self.save()
        return True

    def last_death(self) -> dict | None:
        return self.deaths[-1] if self.deaths else None

    def death_on_floor(self, depth: int) -> dict | None:
        for d in reversed(self.deaths):
            if int(d.get("floor", 0)) == depth:
                return d
        return None

    def record_death(self, floor: int, cause: str, player) -> None:
        weapon = player.weapon.name if player.weapon else "mains nues"
        armor = player.armor.name if player.armor else "aucune"
        self.deaths.append({
            "floor": int(floor),
            "cause": str(cause),
            "cycle": self.cycle,
            "weapon": weapon,
            "armor": armor,
            "kills": int(player.kills),
            "gold": int(player.gold),
            "fragments": int(player.fragments),
            "ts": time.time(),
        })
        if len(self.deaths) > 40:
            self.deaths = self.deaths[-40:]
        self.data["cycle"] = self.cycle + 1
        self.data["runs"] = int(self.data.get("runs", 0)) + 1
        self.data["best_depth"] = max(self.best_depth, int(floor))
        self.data["insight"] = min(9, int(self.data.get("insight", 0)) + 1)
        self.save()

    def record_ending(self, key: str) -> None:
        if key not in self.endings:
            self.endings.append(key)
        self.data["best_depth"] = 7
        self.save()

    def reset(self) -> None:
        import copy as _copy
        self.data = _copy.deepcopy(DEFAULT)
        self.data["deaths"] = []
        self.data["inscriptions"] = []
        self.data["endings"] = []
        self.save()
