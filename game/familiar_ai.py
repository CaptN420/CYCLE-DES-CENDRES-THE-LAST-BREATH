"""IA du familier : décisions autonomes, ordres, ciblage et déplacements."""
from __future__ import annotations

from collections import deque

from . import ui
from .familiar import ABILITIES

DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1)]


def _dist(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _cheb(a, b) -> int:
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def take_turn(fam, game) -> None:
    """Un tour de familier — jamais plus d'une action par tour de joueur."""
    if fam is None or getattr(game, "dungeon", None) is None:
        return
    for key in list(fam.cooldowns):
        fam.cooldowns[key] = max(0, fam.cooldowns[key] - 1)

    if not fam.alive:
        note = fam.tick_ko()
        if note:
            game.log(note, ui.MIDGREY)
        return

    # 1. soins et mana
    if fam.hp < fam.max_hp * 0.5:
        note = fam.drink()
        if note:
            game.log(note, ui.GREEN)
    if fam.class_key == "arcaniste":
        note = fam.restock_mana()
        if note:
            game.log(note, ui.CYAN)

    # 2. butin qui lui appartient, sous ses pieds
    game.familiar_pickup()

    # 3. cible
    target = _pick_target(fam, game)
    order = fam.order

    if order == "reste" and target is None:
        return

    if target is not None:
        if _cheb((fam.x, fam.y), (target.x, target.y)) <= 1:
            _attack(fam, game, target)
            return
        if fam.class_key == "arcaniste" and _dist((fam.x, fam.y), (target.x, target.y)) <= 5:
            if _ability(fam, game, target):
                return
        step = _step_toward(game, (fam.x, fam.y), (target.x, target.y), game.player)
        if step:
            fam.x, fam.y = step
            game.familiar_pickup()
        return

    # 4. pas d'ennemi : suivre le joueur / ramasser son butin
    loot = _nearest_own_loot(game, fam)
    if loot is not None and order in ("ramasser", "suivre", "agressif"):
        if (loot["x"], loot["y"]) == (fam.x, fam.y):
            game.familiar_pickup()
            return
        step = _step_toward(game, (fam.x, fam.y), (loot["x"], loot["y"]), game.player)
        if step:
            fam.x, fam.y = step
            game.familiar_pickup()
        return

    p = game.player
    if order != "reste" and _dist((fam.x, fam.y), (p.x, p.y)) > 2:
        step = _step_toward(game, (fam.x, fam.y), (p.x, p.y), None)
        if step:
            fam.x, fam.y = step


def _pick_target(fam, game):
    p = game.player
    reach = {"suivre": 4, "defendre": 6, "agressif": 9, "prudent": 3,
             "reste": 3, "ramasser": 4}.get(fam.order, 4)
    candidates = []
    for mon in game.monsters:
        if not mon.alive or getattr(mon, "spared", False):
            continue
        if (mon.x, mon.y) not in game.visible:
            continue
        d = _dist((fam.x, fam.y), (mon.x, mon.y))
        if d > reach:
            continue
        if fam.order == "prudent" and mon.hp > fam.hp * 2:
            continue
        weight = d
        if fam.order == "defendre":
            weight += _dist((mon.x, mon.y), (p.x, p.y)) * 2
        if mon.boss:
            weight -= 2
        candidates.append((weight, d, mon))
    if not candidates:
        return None
    candidates.sort(key=lambda entry: (entry[0], entry[1]))
    return candidates[0][2]


def _attack(fam, game, mon) -> None:
    if _ability(fam, game, mon):
        return
    game.familiar_attack(mon)


def _ability(fam, game, mon) -> bool:
    ability = fam.cdef["ability"]
    info = ABILITIES.get(ability, {})
    cd = fam.cooldowns.get(ability, 0)
    cost = info.get("cost", 0)
    if cd > 0 or fam.mana < cost:
        return False
    fam.cooldowns[ability] = info.get("cooldown", 4)
    if cost:
        fam.mana -= cost
    if ability == "morsure":
        game.familiar_attack(mon, bonus=4, bleed=True)
        game.log(f"{fam.name} mord {mon.name} et le fait saigner.", ui.RED)
        return True
    if ability == "provocation":
        game.fam_taunt = 4
        game.log(f"{fam.name} provoque : les ennemis le visent.", ui.ORANGE)
        return True
    if ability == "eclair":
        dmg = 10 + fam.level * 2
        if mon.take_damage(dmg):
            game.on_familiar_kill(mon)
        game.log(f"{fam.name} foudroie {mon.name} : {dmg} dégâts.", ui.CYAN)
        return True
    if ability == "oeil":
        game.familiar_reveal()
        game.log(f"{fam.name} scrute l'obscurité : les détours apparaissent.", ui.CYAN)
        return True
    if ability == "garde":
        game.player_guard = 2
        game.log(f"{fam.name} se place devant toi. Le prochain coup sera amorti.", ui.BONE)
        return True
    return False


def _step_toward(game, start, target, avoid=None):
    """BFS court (max 14 pas) ; ne marche jamais sur la case du joueur."""
    if start == target:
        return None
    prev = {start: None}
    queue = deque([start])
    found = False
    while queue:
        cur = queue.popleft()
        if cur == target:
            found = True
            break
        for dx, dy in DIRS:
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in prev or not game.dungeon.walkable(*nxt):
                continue
            if avoid is not None and nxt == (avoid.x, avoid.y) and nxt != target:
                continue
            prev[nxt] = cur
            queue.append(nxt)
        if len(prev) > 400:
            break
    if not found:
        return None
    node = target
    while prev[node] is not None and prev[node] != start:
        node = prev[node]
    if prev.get(node) is None:
        return None
    return node


def _nearest_own_loot(game, fam):
    best = None
    best_d = 99
    for entry in game.ground:
        item = entry["item"]
        if item.owner != "familiar":
            continue
        d = _dist((fam.x, fam.y), (entry["x"], entry["y"]))
        if d < best_d:
            best, best_d = entry, d
    return best if best_d <= 4 else None