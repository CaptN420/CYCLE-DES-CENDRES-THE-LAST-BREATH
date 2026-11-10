"""Chapitre III — THE GOD BEHIND THE SCREEN : données et textes."""
from __future__ import annotations

from dataclasses import dataclass

from . import entities as ent
from . import ui

TITLE = "CHAPITRE III : THE GOD BEHIND THE SCREEN"
SUBTITLE = "« Tu as cherché celui qui contrôlait ton destin. Tu n'aurais pas dû. »"

PROLOGUE = [
    "Peu importe la fin que tu as choisie au chapitre II, une chose est sûre :",
    "le monde a changé.",
    "",
    "Les étoiles disparaissent une par une. Les montagnes changent de forme",
    "pendant la nuit. Les océans coulent parfois vers le ciel.",
    "Les morts ne parlent plus. Les dieux ne répondent plus.",
    "",
    "Et le temps ne fonctionne plus correctement.",
    "",
    "Dans tes rêves, tu vois une pièce blanche. Sans portes, sans fenêtres,",
    "sans plafond. Une silhouette y est assise devant une machine à écrire.",
    "Chaque fois qu'elle écrit, une partie du monde change.",
    "",
    "Une nuit, elle lève la tête et dit :",
    "« Tu n'étais pas censé arriver jusqu'ici. »",
    "",
    "Tu te réveilles dans L'INTERVALLE.",
]

INTERVALLE = [
    "Ce lieu n'est ni un monde ni une dimension. C'est l'espace entre deux réalités.",
    "Le sol est fait de fragments de lieux que tu as traversés.",
    "",
    "Un morceau de la crypte de Vhar. Les ruines de Vhaldor.",
    "Une salle du trône. Les forges divines. Des donjons qui n'ont jamais existé.",
    "",
    "Une voix résonne dans le vide :",
    "",
    "« Tu as détruit les dieux. Tu as libéré les âmes. Tu as traversé le Néant.",
    "  Mais tu n'as toujours pas compris.",
    "  Tout cela n'était qu'une histoire. »",
]

MEMORIES = {
    "sang": {
        "name": "Le Sang de Nhal'Zor",
        "desc": "Résister aux attaques du Néant (-2 dégâts)",
        "effect": "resistance",
    },
    "ebene": {
        "name": "Le Cœur d'Ébène",
        "desc": "Voir les passages cachés (+2 vision)",
        "effect": "sight",
    },
    "kael": {
        "name": "La Mort de Kael",
        "desc": "Invoquer un ancien guerrier [V]",
        "effect": "invoke",
    },
    "eldria": {
        "name": "Le Dernier Regard d'Eldria",
        "desc": "Anticiper les dangers (+1 défense)",
        "effect": "defense",
    },
    "silence": {
        "name": "Le Premier Silence",
        "desc": "Arrêter le temps ennemi [F]",
        "effect": "freeze",
    },
    "page": {
        "name": "La Page Perdue",
        "desc": "Le secret de la Bibliothèque",
        "effect": "secret",
    },
    "nom": {
        "name": "Ton Nom Véritable",
        "desc": "Les mille tombes te reconnaissent",
        "effect": "name",
    },
}

MEMORY_GRANTS = {
    "biblio": "sang",
    "cite": "eldria",
    "tour": "nom",
    "sanctuaire": "page",
    "porte": "silence",
}


@dataclass
class Territory:
    key: str
    name: str
    short: str
    subtitle: str
    boss: ent.MonsterDef
    monsters: list[ent.MonsterDef]
    wall_glyph: str
    floor_glyph: str
    wall_color: int
    floor_color: int
    ambient: list[str]
    stele: str
    npc: str
    pos: tuple[int, int]
    label_left: bool = False
    riddle: bool = False


TERRITORIES: list[Territory] = [
    Territory(
        "biblio", "La Bibliothèque des Histoires Inachevées", "BIBLIOTHÈQUE",
        "les histoires de tous les êtres, y compris les tiennes",
        ent.MonsterDef("Le Bibliothécaire Aveugle", "B", ui.BONE, 145, 16, 150, 1, 1, (), True),
        [
            ent.MonsterDef("Livre sans fin", "b", ui.BONE, 40, 13, 20, 1, 1),
            ent.MonsterDef("Marque-page vivant", "m", ui.PURPLE, 36, 15, 20, 1, 1, ("drain",)),
            ent.MonsterDef("Rature", "r", ui.DARKGREY, 44, 14, 22, 1, 1, ()),
        ],
        "▓", "·", ui.MIDGREY, ui.BONE,
        [
            "Un livre tombe, ouvert à une page qui te décrit.",
            "Les rayonnages s'éloignent quand tu avances.",
            "Chaque titre est un nom que tu as porté.",
            "Une page se tourne toute seule, puis revient.",
        ],
        "« Ici sont rangées toutes les fins possibles. Aucune n'est la tienne. »",
        "seraphine", (7, 3),
    ),
    Territory(
        "cite", "La Cité des Réalités Brisées", "CITÉ",
        "des fragments de mondes qui se traversent",
        ent.MonsterDef("LE DOUBLE", "D", ui.WHITE, 165, 17, 170, 2, 2, ("fast",), True),
        [
            ent.MonsterDef("Toi, version morte", "t", ui.MIDGREY, 46, 16, 24, 2, 2, ("undead",)),
            ent.MonsterDef("Toi, version dieu", "g", ui.GOLD, 50, 17, 26, 2, 2, ()),
            ent.MonsterDef("Toi, version enfant", "e", ui.CYAN, 38, 15, 22, 2, 2, ()),
        ],
        "░", "·", ui.PURPLE, ui.MIDGREY,
        [
            "Une maison est à la fois en ruine et intacte.",
            "Deux rues identiques se croisent au même endroit.",
            "Tu croises un passant qui a ton visage, plus vieux.",
            "Le sol est fait de toits.",
        ],
        "« Toutes les versions de toi ont échoué ici. Certaines sont encore en train d'essayer. »",
        "elia", (37, 3), True,
    ),
    Territory(
        "tour", "La Tour du Temps Mort", "TOUR",
        "le passé, le présent et l'avenir y sont prisonniers",
        ent.MonsterDef("Le Gardien des Secondes", "S", ui.CYAN, 175, 17, 180, 3, 3, ("fast",), True),
        [
            ent.MonsterDef("Seconde volée", "s", ui.CYAN, 44, 15, 24, 3, 3, ("fast",)),
            ent.MonsterDef("Horloge vide", "h", ui.BONE, 52, 14, 26, 3, 3, ()),
            ent.MonsterDef("Enfant que tu fus", "f", ui.GREY, 40, 16, 24, 3, 3, ("drain",)),
        ],
        "▒", "·", ui.BLUE, ui.CYAN,
        [
            "Chaque étage est une année. Les marches montent et descendent.",
            "Tu entends la voix d'Eldria, trois cents ans en arrière.",
            "Une horloge sonne l'heure qu'il n'est pas.",
            "Ton ombre arrive en retard.",
        ],
        "« Mille tombes portent ton nom. Les dates ne s'accordent pas. »",
        "orvan", (6, 12),
    ),
    Territory(
        "sanctuaire", "Le Sanctuaire du Premier Auteur", "SANCTUAIRE",
        "là où la toute première histoire a été écrite",
        ent.MonsterDef("Le Premier Héros", "H", ui.GOLD, 185, 18, 190, 4, 4, (), True),
        [
            ent.MonsterDef("Brouillon de héros", "b", ui.MIDGREY, 48, 16, 26, 4, 4),
            ent.MonsterDef("Page arrachée", "p", ui.BONE, 42, 17, 24, 4, 4, ("drain",)),
            ent.MonsterDef("Rature du premier jet", "r", ui.DARKGREY, 54, 18, 30, 4, 4, ()),
        ],
        "▓", "·", ui.BROWN, ui.GOLD,
        [
            "Le sol est couvert de versions ratées de toi.",
            "Une machine à écrire géante trône, cassée.",
            "Quelqu'un a écrit « encore » mille fois sur le mur.",
            "L'air sent l'encre et la poussière d'os.",
        ],
        "« L'univers a déjà été détruit des milliers de fois. Chaque fois, il recommençait. »",
        "varken", (37, 12), True,
    ),
    Territory(
        "porte", "La Porte Sans Nom", "PORTE",
        "là où l'histoire est censée finir",
        ent.MonsterDef("Le Gardien du Dernier Mot", "G", ui.WHITE, 140, 18, 200, 5, 5, (), True),
        [
            ent.MonsterDef("Mot oublié", "o", ui.PURPLE, 50, 18, 30, 5, 5),
            ent.MonsterDef("Phrase sans fin", "P", ui.CYAN, 46, 19, 28, 5, 5, ("drain",)),
            ent.MonsterDef("Point final", "p", ui.WHITE, 60, 20, 34, 5, 5, ("fast",)),
        ],
        "░", " ", ui.PURPLE, ui.MIDGREY,
        [
            "Une porte immense flotte dans le vide.",
            "Elle n'a ni poignée, ni serrure, ni mur autour.",
            "Des mots tournent autour d'elle comme des mouches.",
            "Le silence ici a une forme.",
        ],
        "« Ce gardien ne meurt pas. Il attend qu'on comprenne. »",
        "", (21, 2), False, True,
    ),
]

TERRITORY_BY_KEY = {t.key: t for t in TERRITORIES}
CHAMBER_POS = (21, 9)

NPCS = {
    "seraphine": {
        "name": "SÉRAPHINE, la Gardienne des souvenirs",
        "glyph": "S", "color": ui.CYAN,
        "lines": [
            "« Je protège les histoires qu'on n'a pas finies. Il y en a beaucoup. »",
            "« J'ai rencontré des milliers de versions de toi. Une seule a atteint la fin. »",
            "« Elle n'a pas gagné. Elle a simplement arrêté de jouer. »",
        ],
    },
    "elia": {
        "name": "ELIA, l'enfant hors du récit",
        "glyph": "E", "color": ui.MAGENTA,
        "lines": [
            "Une fillette est assise sur un toit qui n'existe qu'à moitié.",
            "« Je ne suis pas dans le livre », dit-elle. « J'ai vérifié. »",
            "« Je ne sais pas qui m'a écrite. Personne, je crois. »",
        ],
    },
    "orvan": {
        "name": "ORVAN, le Roi des fins",
        "glyph": "O", "color": ui.GOLD,
        "lines": [
            "« Je garde les souvenirs de toutes les fins possibles. »",
            "« Tu veux savoir ce qui serait arrivé si tu avais choisi autrement ? »",
            "Il ouvre une main pleine de cendres qui parlent.",
        ],
    },
    "varken": {
        "name": "VARKEN, le Premier Héros",
        "glyph": "V", "color": ui.GOLD,
        "lines": [
            "« J'étais le premier. Il m'a écrit, puis il m'a laissé tomber. »",
            "« Des milliers d'échecs. Des milliers de recommencements. »",
            "« Je ne veux plus qu'on écrive. Ni toi, ni moi, ni lui. »",
        ],
    },
}

RIDDLE_ANSWERS = [
    ("1", "Obéir à son destin", False),
    ("2", "Choisir ce que personne n'a écrit", True),
    ("3", "Devenir plus puissant que le Créateur", False),
    ("4", "Détruire le livre", False),
]

ANOMALIES = [
    "[ERREUR DE RÉALITÉ]  La pièce se répète. Tu reviens à ton point de départ.",
    "[ERREUR DE RÉALITÉ]  Le cadavre devant toi porte ton visage.",
    "[ERREUR DE RÉALITÉ]  Un ennemi cligne des yeux et réapparaît derrière toi.",
    "[ERREUR DE RÉALITÉ]  Les commandes de déplacement s'inversent.",
    "[ERREUR DE RÉALITÉ]  Une salle que tu as visitée s'efface et devient blanche.",
    "[ERREUR DE RÉALITÉ]  Un marchand vend les objets que tu as perdus dans une autre partie.",
    "[ERREUR DE RÉALITÉ]  Trois versions du même monstre respirent ensemble.",
    "[ERREUR DE RÉALITÉ]  Ton nom change de place dans ta bouche.",
]

AUTHOR_TAUNTS = [
    "« Tu recommences encore. »",
    "« Tu crois toujours que la mort est une porte ? »",
    "« Cette fois, elle est verrouillée. »",
    "« J'ai écrit ta peur avant que tu la ressentes. »",
    "« Chaque cadavre de ce monde est une phrase que j'ai barrée. »",
    "« Tu n'es pas courageux. Tu es relu. »",
]

AUTHOR_LINES = [
    "« Enfin. Je commençais à croire que tu n'y arriverais jamais. »",
    "« Tu as traversé mes trois histoires. Tu as tué mes dieux. »",
    "« Tu as libéré les âmes que j'avais mises là pour tenir le monde debout. »",
    "« Et maintenant tu es devant moi, avec l'air de croire que tu peux écrire. »",
    "« Regarde. »",
]

AUTHOR_RAGE = [
    "« TU N'ÉTAIS QU'UN PERSONNAGE ! »",
    "« JE T'AI DONNÉ UN NOM ! JE T'AI DONNÉ UN MONDE ! »",
    "« JE T'AI DONNÉ UNE HISTOIRE ! »",
    "« ET TU OSES ME DÉFIER ? »",
]

ELIA_REPLY = [
    "ELIA : « Il ne t'appartient pas. »",
    "THE AUTHOR : « TOUT M'APPARTIENT. »",
    "ELIA : « Alors pourquoi as-tu peur ? »",
]

ENDINGS = {
    "createur": {
        "title": "LE NOUVEAU CRÉATEUR",
        "colour": ui.PURPLE,
        "lines": [
            "Tu t'assieds. La chaise est exactement à ta taille.",
            "Le stylo est tiède, comme s'il attendait une main depuis toujours.",
            "",
            "Tu écris une première phrase. Le monde obéit.",
            "Tu écris une deuxième. Les étoiles reviennent, dociles.",
            "",
            "Tu contrôles toutes les réalités maintenant.",
            "Tu n'as plus peur de la mort : tu la relis avant publication.",
            "",
            "Quelque part, très loin, quelqu'un commence à lire.",
        ],
    },
    "page_blanche": {
        "title": "LA PAGE BLANCHE",
        "colour": ui.WHITE,
        "lines": [
            "Tu arraches la dernière page. Puis toutes les autres.",
            "",
            "Le livre se vide. Le monde se vide avec lui.",
            "Les tours, les âmes, les dieux, les auteurs : rien.",
            "",
            "Il ne reste pas le néant — même le néant était écrit.",
            "Il ne reste pas de mot pour le dire.",
            "",
            "Et pourtant, pendant un instant, tu es libre.",
        ],
    },
    "liberte": {
        "title": "LA LIBERTÉ",
        "colour": ui.GOLD,
        "lines": [
            "Tu reposes le stylo sans écrire.",
            "",
            "« Je ne vais pas te remplacer », dis-tu. « Et je ne vais pas écrire",
            "  une nouvelle histoire pour eux. »",
            "",
            "Le livre se ferme. Le Créateur ouvre la bouche, et rien ne sort :",
            "sans lecteur, un auteur n'est qu'un homme qui parle seul.",
            "",
            "Le monde devient imprévisible. Les personnages se trompent,",
            "changent d'avis, vivent des choses inutiles et magnifiques.",
            "Personne ne sait ce qui va arriver. C'est exactement le but.",
        ],
    },
    "elia": {
        "title": "LE SACRIFICE D'ELIA",
        "colour": ui.MAGENTA,
        "lines": [
            "Le seul moyen de refermer le livre sans perdre le monde",
            "est d'effacer la seule chose qui n'y était pas écrite.",
            "",
            "Elia comprend avant toi. Elle sourit, comme toujours.",
            "« C'est bien. J'ai eu une existence qui n'était pas prévue. »",
            "",
            "Elle s'efface lentement, ligne par ligne.",
            "Le monde survit, intact, parfaitement cohérent.",
            "",
            "Et terriblement prévisible.",
        ],
    },
    "prison": {
        "title": "LA PRISON ÉTERNELLE",
        "colour": ui.CYAN,
        "lines": [
            "Tu ne détruis pas le Créateur. Tu écris autour de lui.",
            "",
            "Une phrase, puis cent, puis mille, qui se referment",
            "comme des murs sur un homme qui a oublié comment sortir.",
            "",
            "Il crie longtemps. Puis il écrit. Puis il crie encore.",
            "Tu restes assis à côté de la chaise, gardien d'une prison",
            "dont la porte est un paragraphe.",
            "",
            "Tu ne meurs plus. Tu ne vis plus. Tu relis.",
        ],
    },
    "impossible": {
        "title": "LA FIN IMPOSSIBLE — THE PLAYER",
        "colour": ui.WHITE,
        "lines": [
            "Tu ne prends pas le stylo. Tu ne détruis pas le livre.",
            "Tu regardes le Créateur et tu lui montres Elia.",
            "",
            "« Elle n'a pas été écrite. Moi non plus, maintenant. »",
            "",
            "Tu sors du livre. Pas de la pièce : du livre.",
            "Derrière la page, il y a une lumière qui n'appartient à aucun monde.",
            "",
            "Tu comprends alors que le Créateur n'était pas l'origine.",
            "Il a été écrit lui aussi. Par quelqu'un qui te ressemble.",
            "",
            "Quelqu'un qui joue.",
            "",
            "Tu peux fermer. Tu peux rester. Pour la première fois,",
            "la décision ne t'a pas été donnée : tu la prends.",
        ],
    },
}

ENDING_LABELS = [
    ("1", "createur", "Le Nouveau Créateur — prendre la place de l'Author"),
    ("2", "page_blanche", "La Page Blanche — détruire le livre et tout ce qui s'y trouve"),
    ("3", "liberte", "La Liberté — refuser d'écrire une nouvelle histoire"),
    ("4", "elia", "Le Sacrifice d'Elia — sauver le monde en l'effaçant"),
    ("5", "prison", "La Prison Éternelle — l'enfermer dans son propre récit"),
    ("6", "impossible", "La Fin Impossible — briser toutes les règles (secrète)"),
]

FINAL_SCENE = [
    "Après le dernier mot, il ne reste que le vide.",
    "",
    "Elia est à côté de toi.",
    "",
    "« Alors... c'est terminé ? »",
    "",
    "Tu ne réponds pas. Tu ouvres le livre : il n'y a plus rien.",
    "Aucune histoire. Aucun destin. Aucun événement futur.",
    "",
    "« Qu'est-ce qu'on fait maintenant ? »",
    "",
    "Pour la première fois, personne ne sait ce qui va arriver.",
    "",
    "Elia sourit.",
    "",
    "« C'est bien. J'ai toujours voulu savoir ce que ça faisait de choisir. »",
]

FINAL_BANNER = [
    "THE LAST BREATH",
    "CHAPTER III",
    "THE GOD BEHIND THE SCREEN",
    "",
    "THE AUTHOR HAS BEEN DEFEATED.",
    "THE STORY HAS BEEN ERASED.",
    "THE WORLD IS NO LONGER BOUND BY FATE.",
    "",
    "ELIA IS STILL HERE.",
    "",
    "A NEW WORLD MAY BEGIN.",
    "",
    "THANK YOU FOR PLAYING.",
]

UNKNOWN_ENTITY = [
    "[UNKNOWN ENTITY]",
    "",
    "« Tu peux fermer le jeu maintenant. »",
    "« Mais tu reviendras. »",
]

EPILOGUE_FILE = [
    "FILE: origin_000.txt",
    "",
    "CREATOR STATUS: TERMINATED",
    "WORLD STATUS: UNDEFINED",
    "PLAYER STATUS: ACTIVE",
    "ELIA STATUS: UNKNOWN",
    "EXTERNAL OBSERVER: CONNECTED",
    "",
    "...",
    "",
    "WARNING:",
    "A NEW STORY IS BEING WRITTEN.",
]

SECRET_HINT = [
    "« Le Créateur a écrit le monde.",
    "  Le monde a créé les personnages.",
    "  Mais qui a créé le Créateur ? »",
]

CH1_LEGACY = {
    "sacrifice": "Le monde t'a fait martyr ; ses cloches te protègent encore.",
    "dieu": "Tu as goûté au trône du Néant ; les récits te reconnaissent.",
    "trahison": "Tu as libéré Nhal'Zor ; quelque chose en toi n'a jamais été enfermé.",
    "verite": "Tu as vu ce que tu étais ; les mensonges ont moins de prise.",
    "secret": "Tu as brisé un cycle ; le Créateur n'a pas aimé ça.",
    "aucun": "Aucune fin de ta première histoire n'a été conservée.",
}

CH2_LEGACY = {
    "dernier_dieu": "Les âmes t'ont obéi ; elles se souviennent de ta voix.",
    "silence": "Tu as laissé le Silence revenir ; il te doit une faveur.",
    "aube": "Tu as rendu la mort au monde ; cette fois, elle te craint.",
    "sacrifice_eternel": "Tu as battu comme un cœur ; l'écho est encore là.",
    "verite_interdite": "Tu as vu derrière la paroi ; tu sais qu'un autre lit.",
    "aucun": "Le monde des âmes brisées ne t'a pas laissé de trace.",
}

AUTHOR_REWRITES = [
    (" « Il réécrit tes jambes. » Les commandes s'inversent.", "invert"),
    ("« Il réécrit le décor : une copie de Nhal'Zor apparaît.", "summon"),
    ("« Il réécrit ton geste : ta prochaine attaque ne touchera pas.", "cancel"),
    ("« Il réécrit ta mémoire : tu oublies où est le livre.", "blind"),
    ("« Il réécrit la salle : le livre s'éloigne d'un pas.", "move_book"),
    ("« Il réécrit ta mort : un peu de ta vie s'en va. »", "bleed"),
]