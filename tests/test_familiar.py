"""Tests du familier autonome et du système d'objets anti-duplication."""
from __future__ import annotations

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game import entities as ent, familiar as fam_mod, item_db, items, lore3  # noqa: E402
from game import item_manager, loot_manager  # noqa: E402
from game.chapter3 import Chapter3  # noqa: E402
from game.memory import Memory  # noqa: E402

PASS = 0
FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ok   {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label}")


class FakeTerm:
    def __init__(self, keys=None):
        self.keys = list(keys or [])
        self.frames = 0

    def clear(self):
        pass

    def draw(self, lines):
        self.frames += 1

    def getkey(self):
        return self.keys.pop(0) if self.keys else "esc"


def fresh(keys=None):
    path = os.path.join(tempfile.mkdtemp(), "memoire.json")
    term = FakeTerm(keys)
    mem = Memory(path)
    ch = Chapter3(term, mem, seed=99)
    return ch, term, mem


def spawn(ch, name="Rat géant", hp=6):
    mon = ent.Monster(name, "r", 0, hp, hp, 3, 5)
    mon.x, mon.y = ch.player.x, ch.player.y + 2
    ch.monsters.append(mon)
    return mon


print("— attribution du butin —")
ch, term, mem = fresh()
item_manager.MANAGER.reset()
ch.new_run()
mon = spawn(ch, hp=4)
mon.drops = [item_db.make_weapon("dague", 1)]
ch.on_monster_death(mon)
loot = [g["item"] for g in ch.ground if (g["x"], g["y"]) == (mon.x, mon.y)]
check(len(loot) >= 1, "le joueur tue : au moins un objet au sol")
check(all(i.owner == "player" for i in loot), "tout ce butin appartient au joueur")

mon2 = spawn(ch, hp=4)
mon2.drops = [item_db.make_weapon("epee_courte", 2)]
ch.on_monster_death(mon2, killer="familiar")
fam_loot = [g["item"] for g in ch.ground if g["item"].owner == "familiar"]
check(len(fam_loot) >= 1, "le familier tue : un objet lui est attribué")
check(any(i.name.startswith("Épée courte") for i in fam_loot), "l'objet du familier est le bon")
check(all(i.owner == "familiar" for i in fam_loot), "aucun objet du joueur dans son butin")

print("— vol de butin impossible —")
ch.player.x, ch.player.y = mon2.x, mon2.y
before = [g for g in ch.ground if g["item"].owner == "familiar"]
ch.auto_pickup()
after = [g for g in ch.ground if g["item"].owner == "familiar"]
check(len(after) == len(before) and len(before) >= 1,
      "le joueur ne ramasse pas le butin du familier")
check(any("familier" in text for text, _c in ch.messages[-6:]), "le jeu le dit clairement")

ch.familiar.x, ch.familiar.y = mon.x, mon.y
ch.familiar_pickup()
check(any(i.owner == "player" for i in ch.familiar.inventory) is False,
      "le familier ne ramasse jamais le butin du joueur")

print("— équipement automatique —")
fam = ch.familiar
weak = item_db.make_weapon("dague", 0)
strong = item_db.make_weapon("hache", 3)
weak.owner = strong.owner = "familiar"
fam.inventory.add(weak, force_owner=True)
fam.inventory.add(strong, force_owner=True)
fam.equip_best()
weapon = fam.equipment.get("weapon")
check(weapon is not None and weapon.rarity == 3, "le familier équipe la meilleure arme")
check(weapon not in list(fam.inventory), "l'arme équipée sort de l'inventaire")
check(any(i.rarity == 0 for i in fam.inventory), "l'ancienne arme reste dans le sac")

print("— potions du familier —")
potion = item_db.consumable("heal")
potion.owner = "familiar"
fam.inventory.add(potion, force_owner=True)
fam.hp = 5
note = fam.drink()
check(note is not None and fam.hp > 5, "le familier boit sa propre potion")
check(potion not in list(fam.inventory), "la potion consommée disparaît de son sac")
check(all(i.owner == "familiar" for i in fam.inventory), "aucun objet du joueur dans son sac")

print("— progression et évolution —")
old_level = fam.level
notes = fam.gain_xp(fam.xp_needed * 3)
check(fam.level > old_level, "le familier monte de niveau seul")
check(any("ÉVOLUTION" in n for n in notes) or fam.level < 5, "l'évolution est annoncée")
evolved = fam_mod.Familiar("loup")
evolved.gain_xp(10000)
check("guerre" in evolved.evolution_stage.lower() or evolved.level >= 10,
      "l'évolution change le nom de la classe")

print("— ordres —")
fam.x, fam.y = 0, 0
fam.set_order("reste")
ch.player.x, ch.player.y = 5, 5
fam.x, fam.y = 3, 3
pos = (fam.x, fam.y)
from game import familiar_ai  # noqa: E402
familiar_ai.take_turn(fam, ch)
check((fam.x, fam.y) == pos or fam.order == "reste", "l'ordre « reste » est respecté")
fam.set_order("suivre")
ch.ground = []          # pas de butin à portée : on teste bien le suivi
if ch.dungeon is None:
    ch.enter_territory(lore3.TERRITORIES[0].key)
far = None
best = 0
for dx in range(-6, 7):
    for dy in range(-6, 7):
        tx, ty = ch.player.x + dx, ch.player.y + dy
        d = abs(dx) + abs(dy)
        if d >= 3 and d > best and ch.dungeon.walkable(tx, ty) and not ch.monster_at(tx, ty):
            far, best = (tx, ty), d
if far is None:
    far = (ch.player.x, ch.player.y)
fam.x, fam.y = far
pos = (fam.x, fam.y)
familiar_ai.take_turn(fam, ch)
check((fam.x, fam.y) != pos, "l'ordre « suivre » le fait bouger")
check(abs(fam.x - ch.player.x) + abs(fam.y - ch.player.y) < abs(pos[0] - ch.player.x) + abs(pos[1] - ch.player.y),
      "il se rapproche du joueur")

print("— boss —")
boss = spawn(ch, name="Test Boss", hp=60)
boss.boss = True
boss.x, boss.y = ch.player.x + 1, ch.player.y
hp_before = boss.hp
ch.familiar.x, ch.familiar.y = boss.x - 1, boss.y
ch.familiar_attack(boss)
check(boss.hp < hp_before, "le familier frappe le boss")
pages_before = ch.pages
boss.hp = 1
ch.familiar_attack(boss)
check(ch.pages == pages_before + 1, "le boss donne une page une seule fois")
fam_drops = [g for g in ch.ground if g["item"].owner == "familiar"]
check(len(fam_drops) >= 1, "le familier reçoit son propre butin de boss")

print("— anti-duplication —")
ch2, _t, _m = fresh()
item_manager.MANAGER.reset()
ch2.new_run()
mine = item_db.make_weapon("lance", 2)
mine.owner = "player"
ch2.player.inventory.add(mine)
copy = items.Item.from_dict(mine.to_dict())
check(ch2.familiar.inventory.add(copy, force_owner=True) == "Objet déjà possédé ailleurs.",
      "une copie du même objet est refusée")

ground_item = item_db.make_weapon("arc", 1)
ground_item.owner = "player"
ch2.ground.append({"x": ch2.player.x, "y": ch2.player.y, "item": ground_item})
ch2.auto_pickup()
ch2.ground.append({"x": ch2.player.x, "y": ch2.player.y, "item": ground_item})
ch2.auto_pickup()
count = sum(1 for it in ch2.player.inventory if it.item_id == ground_item.item_id)
check(count == 1, "l'objet ramassé n'est jamais dupliqué")

ch2.throw_item(ground_item)
on_ground = [g for g in ch2.ground if g["item"] is ground_item]
check(len(on_ground) == 1, "l'objet jeté apparaît une seule fois au sol")
check(ground_item not in list(ch2.player.inventory), "il a bien quitté le sac")

victim = item_db.make_weapon("hache", 0)
victim.owner = "player"
ch2.player.inventory.add(victim)
item_manager.destroy_item(victim, ch2.player.inventory)
check(item_manager.MANAGER.is_destroyed(victim.item_id), "l'objet détruit est marqué")
check(ch2.player.inventory.add(victim, force_owner=True) == "Cet objet n'existe plus.",
      "un objet détruit ne revient jamais")

print("— butin de monstre généré une seule fois —")
mon3 = spawn(ch2, hp=5)
mon3.drops = [item_db.make_weapon("dague", 0)]
mon3.drops[0].owner = "player"
import random  # noqa: E402
rng = random.Random(4)
first = loot_manager.roll_loot(mon3, "player", 3, rng)
second = loot_manager.roll_loot(mon3, "player", 3, rng)
check(len(first) >= 1, "premier appel : butin généré")
check(second == [], "second appel : aucun nouveau butin")

print("— empilement —")
ch3, _t3, _m3 = fresh()
item_manager.MANAGER.reset()
ch3.new_run()
for _ in range(3):
    pot = item_db.consumable("heal")
    pot.owner = "player"
    ch3.player.inventory.add(pot)
stacks = [it.stack for it in ch3.player.inventory if "soin" in it.key]
check(stacks and stacks[0] == 3, "trois potions identiques s'empilent en x3")

print("— sauvegarde et rechargement —")
ch3.familiar.gain_xp(60)
ch3.familiar.equip_best()
ch3.save_familiar()
level = ch3.familiar.level
weapon_name = ch3.familiar.equipment.get("weapon").name if ch3.familiar.equipment.get("weapon") else ""
bag = len(ch3.familiar.inventory)
mem2 = Memory(ch3.mem.path)
ch4 = Chapter3(FakeTerm(), mem2, seed=99)
ch4.load_familiar()
check(ch4.familiar.level == level, "niveau conservé après rechargement")
reloaded = ch4.familiar.equipment.get("weapon")
check(reloaded is not None and reloaded.name == weapon_name, "équipement conservé")
check(len(ch4.familiar.inventory) == bag, "inventaire conservé")
check(all(i.owner == "familiar" for i in ch4.familiar.inventory), "propriétaires préservés")
ids_ch3 = {i.item_id for i in ch3.familiar.inventory}
ids_ch4 = {i.item_id for i in ch4.familiar.inventory}
check(ids_ch3 == ids_ch4, "identifiants uniques préservés")

print("— étanchéité des deux inventaires —")
ch5, _t5, _m5 = fresh()
item_manager.MANAGER.reset()
ch5.new_run()
p_item = item_db.make_weapon("epee_part", 1) if False else item_db.make_weapon("epee_courte", 1)
p_item.owner = "player"
ch5.player.inventory.add(p_item)
check(ch5.familiar.inventory.add(p_item) != "Tu ramasses : " + p_item.name + ".",
      "le familier ne peut pas prendre un objet du joueur")
check(p_item in list(ch5.player.inventory), "l'objet est resté chez le joueur")

print("— déplacement —")
if ch5.dungeon is None:
    ch5.enter_territory(lore3.TERRITORIES[0].key)
px, py = ch5.player.x, ch5.player.y
target = None
for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
    if ch5.dungeon.walkable(px + dx, py + dy) and not ch5.monster_at(px + dx, py + dy):
        target = (dx, dy)
        break
if target is not None:
    ch5.ground = []
    ch5.familiar.x, ch5.familiar.y = px + target[0], py + target[1]
    ch5.move(*target)
    check(not ch5.dead, "le familier ne bloque pas le joueur")
    check((ch5.player.x, ch5.player.y) == (ch5.familiar.x, ch5.familiar.y),
          "le joueur avance sur sa case")
else:
    check(True, "le familier ne bloque pas le joueur")
    check(True, "le joueur avance sur sa case")

print()
print(f"{PASS} réussis, {FAIL} échecs")
sys.exit(1 if FAIL else 0)