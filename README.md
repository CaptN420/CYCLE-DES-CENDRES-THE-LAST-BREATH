# CYCLE DES CENDRES

Roguelike ASCII en Python (terminal Windows), inspiré de NetHack.
**Trois chapitres** : la crypte de Nhal'Zor, le monde des âmes brisées, puis
l'Intervalle — derrière la page.
Génération procédurale, combats au tour par tour, inventaire, boss, événements
narratifs, mort permanente — et un monde qui se souvient de chacune de vos morts.

Au lancement, un menu propose :

- `[1]` **Chapitre I — Les Échos du Dernier Souffle** : 7 étages, Nhal'Zor, 5 fins.
- `[2]` **Chapitre II — Le Royaume des Âmes Brisées** : 6 régions ouvertes,
  le Premier Silence, 5 fins, et l'héritage réel de votre fin du chapitre I.
- `[3]` **Chapitre III — The God Behind the Screen** : 5 territoires de
  l'Intervalle, THE AUTHOR, 6 fins dont une secrète, et un Créateur qui
  réécrit les règles pendant que vous jouez.

## Comment ce jeu a été fait

Projet **vibecoding** assumé, et documenté sans détour :

- **prompts de design rédigés avec GPT** (univers, chapitres, mécaniques,
  contraintes de fiabilité) — le prompt d'origine du chapitre I est dans
  [`Prompt/Gpt_prompt.txt`](Prompt/Gpt_prompt.txt) ;
- **code cuisiné avec DeepSeek V4.1 Flash**, piloté via l'agent Hermes
  (Nous Research) : implémentation, intégration aux trois chapitres, chasse aux
  bugs en exécution réelle ;
- **direction, arbitrages et validation humaines** : 40 objets utiles plutôt
  que 300 inutiles, deux inventaires strictement séparés, et 183 vérifications
  automatisées avant d'annoncer quoi que ce soit.

Détail complet dans [`CREDITS.md`](CREDITS.md).

## Le familier (compagnon autonome)

Chaque chapitre peut être traversé **à deux**. Le familier est un second
aventurier complet, pas un bonus de statistiques.

- **Cinq classes** : loup, golem, arcaniste, corbeau, chevalier spectral —
  chacune avec ses statistiques, sa compétence et ses préférences d'équipement.
- **Deux inventaires, deux équipements, deux progressions** : le familier
  ramasse son propre butin, équipe ses propres pièces (9 emplacements), boit
  ses propres potions, gagne de l'expérience et évolue (5 paliers par classe).
- **IA autonome** : suit le joueur, évite les pièges connus, cible les ennemis
  dangereux, protège le joueur, recule quand il est blessé, ramasse ce qui lui
  appartient, ne reste pas coincé dans les couloirs, n'agit qu'une fois par tour.
- **Butin séparé** : le loot d'un monstre appartient à celui qui le tue. Le
  joueur ne peut pas ramasser un objet du familier et inversement — les
  échanges passent uniquement par `[D] donner` / `[R] prendre`.
- **Ordres** : `suivre`, `defendre`, `agressif`, `prudent`, `reste`, `ramasser`.
  Ils changent les priorités, jamais l'autonomie.
- **Persistance** : nom, classe, niveau, XP, statistiques, équipement,
  inventaire, compétences, ordres et historique sont sauvegardés dans
  `save/memoire.json` (clé `familiar`) et retrouvés à l'identique.

Touche `[P]` : statistiques, équipement, sac, compétences, historique, ordres,
échanges. `[H]` (chapitre III) boit une potion de soin du joueur.

### Fiabilité des objets

- identifiant unique par objet (`item_id`) + propriétaire + localisation ;
- états exclusifs : `INVENTORY_PLAYER`, `INVENTORY_FAMILIAR`, `GROUND`,
  `EQUIPPED_PLAYER`, `EQUIPPED_FAMILIAR`, `STORAGE`, `DESTROYED` ;
- un objet détruit ne revient jamais (pierre tombale), un objet jeté reste au
  sol avec son propriétaire, les butins de monstre ne sont générés qu'une fois
  (`loot_generated`), les doublons d'identifiant sont refusés au chargement.

Modules : `game/item_db.py` (40 objets, 5 raretés), `game/item_manager.py`
(registre, inventaires, équipement), `game/loot_manager.py` (attribution),
`game/familiar.py`, `game/familiar_ai.py`, `game/familiar_field.py`
(intégration aux trois chapitres).

## Lancer le jeu

Double-cliquez sur **`Lancer_Le_Jeu.bat`**.

Le lanceur :
- passe la console en UTF-8 (`chcp 65001`) pour les accents et les cadres ;
- cherche `py -3` puis `python` ;
- règle la fenêtre en 84x34 et lance `main.py`.

Prérequis : Python 3.9+ (testé avec Python 3.14). Aucune dépendance externe.

En ligne de commande :

```
cd RogueLike
py -3 main.py
```

## Commandes

| Touche | Action |
|---|---|
| `WASD`, flèches, `hjkl`/`yubn` | se déplacer (diagonales avec y/u/b/n) |
| marcher sur un monstre | attaquer |
| `E` | interagir (coffre, inscription, sanctuaire, trône) |
| `I` | ouvrir le sac (équiper / boire / lire) |
| `G` | ramasser l'objet sous ses pieds |
| `R` | souffler (chapitre III : hors du temps, hors du hub) |
| `V` / `F` | invoquer un souvenir / arrêter le temps (chapitre III) |
| `Entrée` ou `>` | descendre quand on est sur l'escalier |
| `R` | attendre un tour |
| `?` | aide |
| `Q` | quitter la partie (le cycle reste en cours) |

## Le donjon

| Étage | Lieu | Ambiance |
|---|---|---|
| 1 | Les Cellules Oubliées | rats, prisonniers morts, gardiens squelettes |
| 2 | La Forêt Souterraine | champignons vivants, araignées, plantes carnivores |
| 3 | La Cité Engloutie | marchands noyés, automates, spectres nains — **boss : Roi Nain Maudit** |
| 4 | La Bibliothèque des Morts | livres hurlants, bibliothécaires, ombres |
| 5 | Les Forges Infernales | démons, forgerons immortels — **boss : Seigneur des Forges** |
| 6 | Le Sanctuaire des Dieux | statues, anges déchus — **boss : Gardien du Sanctuaire** |
| 7 | Le Trône du Néant | **Nhal'Zor**, puis le choix final |

Chaque étage contient **un coffre avec un fragment divin**, une ou deux
inscriptions, parfois un sanctuaire, et un escalier vers l'étage suivant.
Accumuler les **sept fragments** ouvre la fin secrète.

## Les classes

Au premier cycle, choisissez votre visage :

| Classe | Bonus | Équipement initial |
|---|---|---|
| **Gardien** | +4 PV max, attaque +1 | Armure de cuir usé |
| **Rôdeur** | Dégâts +1, +1 intuition immédiate | — |
| **Sorcier** | -2 PV max, insight +1 | Parchemin de flammes |

## La mémoire du donjon

La mémoire est stockée dans `save/memoire.json` (créé au premier lancement,
supprimable depuis l'écran-titre avec `R`).

À chaque mort :

- le donjon est **régénéré** au cycle suivant (monstres et objets replacés) ;
- la mort est enregistrée (étage, cause, arme, armure, butin) ;
- un **squelette portant votre ancienne arme et armure** réapparaît à
  l'étage où vous êtes mort et vous attaque ;
- vous gagnez **1 point d'intuition** (conservé entre les cycles) ;
- les **inscriptions lues restent lues** : le texte s'ajoute à votre mémoire.

L'intuition n'est pas décorative :

| Intuition | Compétence | Effet |
|---|---|---|
| 3 | **Se Souvenir** | Les squelettes attaquent 10% moins fort |
| 5 | **Mémoriale** | +1 PV max permanent par cycle après le 2e |
| 7 | **Écho Vivant** | Tu prévisualises les déplacements des monstres (1 tour) |
| 9 | **Dernier Souffle** | Quand tu meurs, tu ressuscites avec 5 PV (une fois par cycle) |

- à partir de 5 points, l'option **La Vérité** apparaît sur le trône ;
- à partir de 6 points, vous commencez chaque cycle avec **+4 PV max** ;
- certaines rencontres (fantômes, mendiants, ennemis épargnés) en donnent aussi.

## Les cinq fins

| Fin | Condition |
|---|---|
| Le Sacrifice | vaincre Nhal'Zor et choisir de mourir avec lui |
| Le Nouveau Dieu | prendre sa place sur le trône |
| La Trahison | le libérer et le servir |
| La Vérité | 5 points d'intuition ou plus, puis lire ce que vous êtes |
| Briser le cycle | porter les **7 fragments divins** et les assembler |

## Événements

Whispers du Néant, fantôme qui vous reconnaît, cadavre d'un ancien « vous »,
marchand maudit (objets parfois corrompus), squelette mendiant, caches d'or,
squelette qui te reconnaît et te donne un cœur.

### Quêtes secrètes

- **Cœur de squelette** — drop rare des squelettes (15% de chance), item quest
  qui déclenche un événement unique au trône.
- **Clé noire activée** — à 7 fragments + intuition 5, la clé brille et révèle
  le chemin vers le trône.

## Chapitre II — Le Royaume des Âmes Brisées

Trois cents ans après la crypte, la machine divine s'est arrêtée : les âmes ne
peuvent plus partir. Le joueur se réveille dans un cercle de runes, sans cœur
qui bat, avec le **Cœur d'Ébène** (1er des 7 fragments).

### Les six régions

| Région | Boss | Particularité |
|---|---|---|
| Les Ruines de Vhaldor | Le Roi sans Visage | Kael, le chevalier sans mort, te traque |
| La Forêt des Murmures | La Mère des Racines | Lyra, l'enfant qui se souvient, te soigne |
| Le Royaume Gelé de Skäar | Le Gardien de l'Hiver | Morvan, le marchand des âmes, commercera |
| La Nécropole des Rois | L'Empereur des Mille Âmes | Aureth, le dieu déchu, propose un pacte |
| Les Forges du Premier Monde | Le Forgeron Primordial | on y apprend d'où viennent les humains |
| L'Au-delà des Dieux | L'Écho du Premier Silence | les souvenirs deviennent des lieux |

Chaque région contient un **boss** (qui laisse un **fragment**), une **stèle**
(+1 savoir) et un **PNJ**. Il faut les 7 fragments pour ouvrir L'Origine,
dernier donjon et combat contre **LE PREMIER SILENCE**.

### Le savoir et les souvenirs

- **Souvenirs** : monnaie persistante. +3 par boss, dépensés chez Morvan
  (3 = potions + parchemin, 6 = arme).
- **Savoir** (0-4) : stèles, Lyra, refus du pacte d'Aureth, ou 5 morts.
  À 4, la cinquième fin (**La Vérité Interdite**) se déverrouille.
- **Kael** : le combattre (duel) ou payer 3 souvenirs. Allié, il retire
  40 PV au boss final. **Aureth** : accepter son pouvoir (+8 PV, +3 attaque)
  renforce le boss final de 50 PV — il t'a menti.

### La mort change le monde

Chaque mort du chapitre II est enregistrée (région, cause, équipement) :

| Morts | Conséquence permanente |
|---|---|
| 1 | une âme quitte ton corps (Souffle errant dans la région suivante) |
| 2 | les PNJ commencent à te reconnaître |
| 3 | des ennemis portent ton ancien équipement (Écho équipé) |
| 5 | **ton reflet** se détache et t'attaque |
| 10 | le Premier Silence te parle directement |

### Les cinq fins du chapitre II

| Fin | Décision |
|---|---|
| Le Dernier Dieu | prendre le contrôle de L'Origine |
| Le Grand Silence | libérer le Premier Silence |
| La Dernière Aube | détruire L'Origine et rendre la mort aux âmes |
| Le Sacrifice Éternel | devenir le cœur de la machine |
| La Vérité Interdite | refuser le choix et voir derrière (savoir 4/4) |

Après toute fin : scène finale, puis déblocage du souvenir **LE CRÉATEUR**
(teaser du chapitre III).

### Commandes du chapitre II

| Touche | Action |
|---|---|
| `WASD` / flèches | carte du monde : choisir une région — en région : se déplacer |
| `1`-`6` | sélection directe d'une région |
| `E` / `Entrée` | entrer dans la région / interagir (stèle, PNJ, cœur) |
| `<` | revenir à la carte du monde |
| `I` | sac · `O` journal · `R` attendre · `?` aide · `Q` quitter |

## Structure du projet

```
RogueLike/
├── Lancer_Le_Jeu.bat      lanceur Windows
├── main.py                point d'entrée, gestion des erreurs
├── game/
│   ├── ui.py              couleurs ANSI 256, cadres, clavier (msvcrt)
│   ├── lore.py            chapitre I : étages, inscriptions, murmures, fins, compétences
│   ├── items.py           armes, armures, potions, parchemins, butin (I et II)
│   ├── entities.py        joueur (avec classes), monstres, tables par profondeur
│   ├── dungeon.py         génération (pièces + couloirs), champ de vision
│   ├── memory.py          mémoire persistante JSON (morts, intuition, fins, chapitre II)
│   ├── game.py            chapitre I : boucle, rendu, combats, événements, fins
│   ├── lore2.py           chapitre II : régions, PNJ, héritages, fins, scène finale
│   ├── chapter2.py        chapitre II : carte du monde, régions, échos, fins
│   └── menu.py            menu principal (choix du chapitre)
├── save/memoire.json      créé au premier lancement
└── tests/
    ├── test_game.py       18 tests réels du chapitre I
    ├── test_chapter2.py   13 tests réels du chapitre II
    ├── preview.py         aperçus texte des écrans du chapitre I
    ├── preview2.py        aperçus texte des écrans du chapitre II
    ├── apercus.txt        rendu ASCII (chapitre I)
    └── apercus2.txt       rendu ASCII (chapitre II)
```

## Tests

```
cd RogueLike
py -3 tests/test_game.py
py -3 tests/test_chapter2.py
```

Chapitre I : connectivité des 7 donjons sur 30 graines, géométrie du cadre
(79 colonnes), 300 tours simulés, combat/XP/butin, coffre et fragments,
persistance de la mémoire sur disque, retour du squelette avec l'équipement du
cycle précédent, descente 1→7, verrouillage des fins, inventaire, classes,
compétences, Dernier Souffle.

Chapitre II : cadre 79x28 sur la carte du monde et les 6 régions, présence du
boss / de la stèle / du PNJ / de la sortie, récompense de boss (fragment +
souvenirs + savoir), persistance de la stèle, commerce de Morvan, duel de Kael
et recrutement, enregistrement des morts et apparition des échos, route
complète vers les 4 fins et la Vérité Interdite verrouillée/déverrouillée,
scène finale et déblocage de LE CRÉATEUR, héritage du chapitre I, menu,
300 tours simulés.

Chapitre III : cadre 79x28 sur le hub et les 5 territoires, énigme du Gardien
du Dernier Mot, butin de boss (page + souvenir), Varken épargné ou achevé,
salle secrète de la Bibliothèque, mille tombes, mort qui retire un souvenir et
réveille le Créateur, anomalies de réalité, chambre de l'Author, trois
écritures, offre du Créateur, verrouillage de la fin secrète, fins enregistrées,
épilogue `origin_000.txt`.

Crédits et méthode : [`CREDITS.md`](CREDITS.md).

Aperçus des écrans :

```
py -3 tests/preview.py
py -3 tests/preview2.py
py -3 tests/preview3.py
```

Partie automatique (sonde de difficulté + vérification d'intégration) :

```
py -3 tests/autoplay3.py
```
