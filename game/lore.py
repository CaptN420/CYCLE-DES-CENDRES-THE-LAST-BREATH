"""Univers, textes et tables narratives de Nhal'Zor."""
from __future__ import annotations

TITLE = "CYCLE DES CENDRES"

INTRO = [
    "Il y a mille ans, sept dieux régnaient sur le monde.",
    "Le septième, Nhal'Zor, découvrit que l'humanité n'était",
    "qu'un élevage : les six autres se nourrissaient de vos âmes.",
    "",
    "Il assassina ses frères et plongea le monde dans la nuit.",
    "Les derniers mages scellèrent son âme sous les montagnes",
    "de Vhar. Ils y laissèrent leur vie — et leur descendance.",
    "",
    "Tu te réveilles dans une cellule. Tu ne te souviens de rien.",
    "Dans ta main : une vieille clé noire.",
    "",
    "— Choisis ton visage —",
    "",
    "  [G]ardien   ·   +4 PV, armure de cuir, attaque +1",
    "  [R]ôdeur    ·   +1 intuition immédiate, dégâts +1",
    "  [S]orcier   ·   -2 PV, parchemin de feu, insight +1",
]

WALL_MESSAGE = [
    "« Tu es déjà venu ici.",
    "  Tu es déjà mort ici.",
    "  Et tu reviendras encore. »",
]


class FloorTheme:
    def __init__(self, depth: int, name: str, subtitle: str, wall_color: int,
                 floor_color: int, ambient: list[str]):
        self.depth = depth
        self.name = name
        self.subtitle = subtitle
        self.wall_color = wall_color
        self.floor_color = floor_color
        self.ambient = ambient


THEMES: dict[int, FloorTheme] = {
    1: FloorTheme(
        1, "Les Cellules Oubliées", "l'odeur du fer et du vieux sang", 242, 246,
        [
            "Un courant d'air froid traverse la salle.",
            "Une chaîne rouillée pend depuis le plafond.",
            "Des ongles ont griffé la pierre, encore et encore.",
            "Au loin, une porte claque. Personne ne l'a touchée.",
        ],
    ),
    2: FloorTheme(
        2, "La Forêt Souterraine", "un souffle végétal, humide", 28, 64,
        [
            "Des spores luisent doucement dans l'obscurité.",
            "Quelque chose rampe sous les racines.",
            "Un champignon se tourne vers toi, lentement.",
            "L'air sent le compost et le sucre pourri.",
        ],
    ),
    3: FloorTheme(
        3, "La Cité Engloutie", "l'eau monte jusqu'aux chevilles", 30, 39,
        [
            "Une cloche sonne sous l'eau, étouffée.",
            "Des fenêtres naines s'allument puis s'éteignent.",
            "Une machine répète le même geste depuis mille ans.",
            "Une pièce de monnaie flotte à la surface.",
        ],
    ),
    4: FloorTheme(
        4, "La Bibliothèque des Morts", "le parchemin sec et la cire froide", 94, 180,
        [
            "Un livre tombe. Personne ne l'a poussé.",
            "Des pages tournent toutes seules, quelque part.",
            "Tu entends ta propre voix lire à haute voix.",
            "L'encre suinte des rayonnages comme du sang noir.",
        ],
    ),
    5: FloorTheme(
        5, "Les Forges Infernales", "la chaleur et le métal qui hurle", 130, 166,
        [
            "L'enclume résonne. Le forgeron n'a plus de mains.",
            "Des étincelles dessinent un visage dans l'air.",
            "Une lame inachevée tremble sur son support.",
            "Le sol est tiède, comme une peau.",
        ],
    ),
    6: FloorTheme(
        6, "Le Sanctuaire des Dieux", "un silence qui écoute", 60, 189,
        [
            "Six statues. Six visages tournés vers toi.",
            "Un cierge s'allume sans flamme.",
            "L'écho de tes pas arrive avant toi.",
            "Tu jures entendre quelqu'un prier ton nom.",
        ],
    ),
    7: FloorTheme(
        7, "Le Trône du Néant", "le vide qui respire", 53, 54,
        [
            "Il n'y a plus de murs. Seulement des morceaux de nuit.",
            "Quelque chose d'immense se penche pour te voir.",
            "Ton ombre s'allonge vers le trône, sans toi.",
            "Tu entends le bruit d'un cœur qui n'est pas le tien.",
        ],
    ),
}

FLOOR_NAMES = {d: t.name for d, t in THEMES.items()}

# Inscriptions gravées : 3 par étage, révélées au fil des cycles.
INSCRIPTIONS: dict[int, list[str]] = {
    1: [
        "« Ici dormaient ceux qui t'ont précédé. Ils portaient ton visage. »",
        "« La clé noire n'ouvre aucune porte. Elle te désigne. »",
        "« Cycle 7 : il a mangé le pain. Cycle 8 : il a mangé le gardien. »",
    ],
    2: [
        "« Les racines se nourrissent de ce que tu oublies. »",
        "« Ne cueille pas le champignon qui te ressemble. »",
        "« Elle t'a attendu sous la forêt. Elle attend encore. »",
    ],
    3: [
        "« Les nains ont bâti cette cité pour cacher une seule porte. »",
        "« Le gardien du troisième étage fut ton frère. Tu l'as tué trois fois. »",
        "« L'eau se souvient mieux que les dieux. »",
    ],
    4: [
        "« Chaque livre de cette salle raconte une de tes morts. »",
        "« Page 12 : l'empoisonnement. Page 13 : la noyade. Page 14 : toi, maintenant. »",
        "« Les bibliothécaires ne lisent pas. Ils collectionnent. »",
    ],
    5: [
        "« Les forgerons immortels forgent la même lame depuis mille ans. »",
        "« Cette lame a un nom : Dernier Souffle. Elle attend un porteur. »",
        "« Le feu ne brûle pas les dieux. Il les révèle. »",
    ],
    6: [
        "« Six dieux sont morts ici. Six statues. Six menteurs. »",
        "« Nhal'Zor ne fut pas le traître. Il fut le seul honnête. »",
        "« Tu n'es pas leur descendant. Tu es leur œuvre. »",
    ],
    7: [
        "« Le trône n'est pas vide. Il t'attend depuis toujours. »",
        "« Sept fragments. Une seule volonté pour les briser. »",
        "« Tu es déjà venu ici. Cette fois, souviens-toi. »",
    ],
}

WHISPERS = [
    "[Un murmure traverse les murs...]  « Tu portes encore son visage... »",
    "[Quelque chose t'observe.]",
    "[Une voix inconnue]  « Ne tue pas le gardien du troisième étage. Il était ton frère. »",
    "[Un murmure traverse les murs...]  « Combien de fois encore ? »",
    "[Quelque chose t'observe.]  « Tu as déjà dit non, la dernière fois. »",
    "[Une voix inconnue]  « Le trône se souvient de ton poids. »",
    "[Un murmure traverse les murs...]  « Tu n'es pas revenu. Tu n'es jamais parti. »",
    "[Quelque chose t'observe.]  « Elle compte. Les morts comptent. »",
    "[Un souffle froid]  « Le rôdeur d'avant aurait fait mieux. »",
    "[La pierre tremble]  « Il y a un autre chemin. Tu l'as déjà pris. Tu as échoué. »",
    "[Quelque chose te touche l'épaule.]  « Je suis toi. Demain, tu seras moi. »",
    "[Une cloche lointaine]  « Le gardien dort encore. Ne le réveille pas comme la fois dernière. »",
]

# Nouvelles inscriptions (à ajouter au fil des cycles)
INSCRIPTIONS_BONUS: dict[int, list[str]] = {
    1: [
        "« Le premier à mourir était un rôdeur. Il portait encore son arc. »",
        "« Un sorcier est monté jusqu'au trône. Il a refusé de s'asseoir. »",
        "« La clé noire pèse plus lourd quand on a tué son propre squelette. »",
    ],
    2: [
        "« Les champignons murmurent le nom de celui qui va mourir ensuite. »",
        "« Tu as déjà cueilli celui-ci. Tu t'es trompé, la dernière fois. »",
        "« La forêt est un corps. Tu marches sur sa peau. »",
    ],
    3: [
        "« Le Roi Nain Maudit portait encore son anneau de forgeron. »",
        "« L'eau a volé sept visages. Elle en garde huit. »",
        "« Les automates ne sont pas des machines. Ce sont des prisonniers. »",
    ],
    4: [
        "« Le bibliothécaire en pleurs est ton ancêtre. Tu ne l'as pas encore rencontré. »",
        "« Page 47 : le sorcier a lu ce livre avant toi. Il s'est arrêté à la page 12. »",
        "« L'encre de ce livre est faite de cendres. Les tiennes, peut-être. »",
    ],
    5: [
        "« La lame inachevée porte ton nom gravé à l'envers. »",
        "« Le Seigneur des Forges a forgé la tienne. Il se souvient de ta main. »",
        "« Chaud. Trop chaud. C'est ça, le vrai feu. Pas celui-ci. »",
    ],
    6: [
        "« La statue qui pleure est la sixième. Elle pleure pour toi. »",
        "« L'ange déchu t'a déjà parlé. Tu as fermé les oreilles. »",
        "« Le prêtre du Néant porte encore ta marque sur son front. »",
    ],
    7: [
        "« Nhal'Zor attend depuis si longtemps qu'il a oublié pourquoi. »",
        "« Les sept fragments forment un miroir. Tu ne veux pas te regarder dedans. »",
        "« Le trône est chaud. Il a gardé ta chaleur. Celle du cycle d'avant. »",
    ],
}

# Compétences débloquées par l'intuition
SKILLS = {
    3: {
        "name": "Se Souvenir",
        "desc": "Les squelettes attaquent 10% moins fort.",
        "effect": "skeleton_weaken",
    },
    5: {
        "name": "Mémoriale",
        "desc": "+1 PV max permanent par cycle après le 2e.",
        "effect": "cycle_hp_bonus",
    },
    7: {
        "name": "Écho Vivant",
        "desc": "Tu prévisualises les déplacements des monstres (1 tour).",
        "effect": "enemy_preview",
    },
    9: {
        "name": "Dernier Souffle",
        "desc": "Resurrection une fois par cycle avec 5 PV.",
        "effect": "last_breath",
    },
}

GAME_OVER_QUOTES = [
    "Le donjon garde ton empreinte.",
    "Un autre « toi » se réveillera dans la cellule.",
    "Nhal'Zor sentit quelque chose de familier mourir.",
    "La crypte se referme. Elle s'ouvrira encore.",
]

ENDING_TEXTS: dict[str, dict[str, object]] = {
    "sacrifice": {
        "title": "LE SACRIFICE",
        "colour": 196,
        "lines": [
            "Tu brises le dernier souffle de Nhal'Zor.",
            "Son âme se déchire — et la tienne avec elle,",
            "car vous n'avez jamais été deux.",
            "",
            "Le monde se réveille lentement dans une aube grise.",
            "Les morts se rendorment. Les mages sont vengés.",
            "",
            "Dans la cellule vide, une clé noire attend.",
            "Personne ne vient la reprendre.",
        ],
    },
    "dieu": {
        "title": "LE NOUVEAU DIEU",
        "colour": 141,
        "lines": [
            "Tu t'assieds sur le trône. Le Néant t'accueille",
            "comme un vieil ami qui n'attendait que toi.",
            "",
            "Les sept étages se plient sous ta pensée.",
            "Tu n'as plus faim. Tu n'as plus peur.",
            "",
            "Mille ans plus tard, un aventurier se réveillera",
            "dans une cellule, une clé noire dans la main.",
            "Tu le regarderas comme on regarde un repas.",
        ],
    },
    "trahison": {
        "title": "LA TRAHISON",
        "colour": 208,
        "lines": [
            "Tu brises les sceaux. Nhal'Zor se relève,",
            "immense et patient, et pose sur toi un regard presque doux.",
            "",
            "« Enfin », dit-il. Ce mot seul fait mourir un royaume.",
            "",
            "Tu deviens son serviteur. Tu ne meurs plus.",
            "Tu ne vis plus non plus.",
            "",
            "Quelque part dans la crypte, un squelette porte ton ancienne",
            "armure et pleure en silence ce que tu as cessé d'être.",
        ],
    },
    "verite": {
        "title": "LA VÉRITÉ",
        "colour": 51,
        "lines": [
            "Tu comprends, enfin, en lisant les murs.",
            "",
            "Tu n'es pas le descendant des mages.",
            "Tu es un fragment de Nhal'Zor, détaché et humanisé",
            "pour comprendre ce qu'il avait détruit.",
            "",
            "Chaque mort t'a rapproché de lui. Chaque cycle",
            "t'a appris à l'aimer un peu plus.",
            "",
            "Tu ne le combats pas. Tu le rejoins.",
            "La crypte n'est pas une prison. C'est un berceau.",
        ],
    },
    "secret": {
        "title": "BRISER LE CYCLE",
        "colour": 220,
        "lines": [
            "Les sept fragments divins s'assemblent dans ta main.",
            "Ils ne forment pas une arme, ni une couronne,",
            "ni une clé. Ils forment un souvenir.",
            "",
            "Le tien. Celui d'avant les dieux, d'avant la crypte,",
            "d'avant le Néant. Un nom.",
            "",
            "Tu le prononces. Nhal'Zor s'arrête — non pas vaincu,",
            "mais reconnu. Il s'effondre en poussière de nuit.",
            "",
            "Pour la première fois depuis mille ans,",
            "la cellule est vide. Vraiment vide.",
            "Tu peux partir.",
        ],
    },
}

ENDING_JOURNAL: dict[str, str] = {
    "sacrifice": "Le Sacrifice — tu as détruit Nhal'Zor et péri avec lui.",
    "dieu": "Le Nouveau Dieu — tu as pris sa place sur le trône.",
    "trahison": "La Trahison — tu as libéré Nhal'Zor et l'as servi.",
    "verite": "La Vérité — tu as compris ce que tu étais.",
    "secret": "La Fin secrète — tu as brisé le cycle des morts.",
}
