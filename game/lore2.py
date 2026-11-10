"""Chapitre II — univers, régions, personnages, fins."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import entities as ent
from . import ui

TITLE = "CHAPITRE II : LE ROYAUME DES ÂMES BRISÉES"
SUBTITLE = "« Les dieux craignaient la mort. Les hommes craignaient les dieux. »"

PROLOGUE = [
    "Trois cents ans se sont écoulés depuis la crypte.",
    "",
    "Le monde n'est plus celui que tu connaissais. Les royaumes ont disparu,",
    "les grandes cités sont des cimetières, les océans sont couverts d'une",
    "brume noire. Le soleil ne se lève plus tout à fait.",
    "",
    "Quand la machine divine s'est arrêtée, les âmes ont cessé d'être aspirées.",
    "Les morts ne disparaissent plus. Ils restent. Ils s'accumulent,",
    "se déforment, oublient. Certaines possèdent les vivants.",
    "",
    "Les survivants appellent cette époque l'Ère des Âmes Brisées.",
    "",
    "Tu te réveilles dans un cercle de runes. Ta peau est froide.",
    "Ton cœur ne bat plus. Tu ne respires pas.",
]

ELDRIA_INTRO = [
    "Une vieille femme aveugle recule en te voyant.",
    "",
    "« Non... Ce n'est pas possible... »",
    "« Nous avions détruit son corps... »",
    "« Les anciens textes disaient que tu ne reviendrais jamais. »",
    "",
    "Elle baisse la tête.",
    "",
    "« Trois cents ans... Cela fait trois cents ans que le monde attend ton retour. »",
    "",
    "Elle te tend un objet : un fragment noir et tiède, qui bat comme un cœur.",
    "« Le Cœur d'Ébène. Un morceau de L'Origine. Six autres existent. »",
    "« Réunis-les et tu retrouveras la machine. Mais ne la réactive pas. »",
    "« Quelque chose dort dedans. Plus ancien que les sept dieux. »",
    "",
    "Elle meurt avant que tu puisses répondre.",
]


@dataclass
class Region:
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
    steles: list[str]
    npc: str
    pos: tuple[int, int]
    label_left: bool = False


REGIONS: list[Region] = [
    Region(
        "vhaldor", "Les Ruines de Vhaldor", "VHALDOR",
        "la capitale des hommes, pleine de cadavres qui répètent leur mort",
        ent.MonsterDef("Le Roi sans Visage", "R", ui.GOLD, 95, 15, 90, 1, 1, (), True),
        [
            ent.MonsterDef("Citoyen qui répète sa mort", "c", ui.MIDGREY, 26, 9, 12, 1, 1),
            ent.MonsterDef("Garde sans tête", "g", ui.BONE, 32, 11, 16, 1, 1, ("undead",)),
            ent.MonsterDef("Âme fracturée", "a", ui.PURPLE, 22, 12, 14, 1, 1, ("drain",)),
        ],
        "▓", "·", ui.MIDGREY, ui.MIDGREY,
        [
            "Un bourgeois salue une foule qui n'existe plus.",
            "Les cloches ont fondu. Personne ne les a remplacées.",
            "Une âme frappe à une porte depuis trois siècles.",
            "Sous tes pieds, les pavés sont tièdes.",
        ],
        [
            "« Ici, chaque mort rejoue son dernier instant. Le Roi, lui, les collectionne. »",
            "« Les prêtres disent que ta venue annonce la fin. Ils n'ont pas tort. »",
        ],
        "kael", (5, 4),
    ),
    Region(
        "foret", "La Forêt des Murmures", "FORÊT",
        "des âmes enracinées qui racontent les souvenirs des morts",
        ent.MonsterDef("La Mère des Racines", "W", ui.GREEN, 110, 14, 100, 2, 2, ("poison",), True),
        [
            ent.MonsterDef("Âme enracinée", "t", ui.DARKGREEN, 30, 10, 15, 2, 2, ("undead",)),
            ent.MonsterDef("Murmure en chœur", "m", ui.MAGENTA, 24, 13, 15, 2, 2, ("poison",)),
            ent.MonsterDef("Loup de sève", "w", ui.GREEN, 34, 12, 18, 2, 2, ("fast",)),
        ],
        "♣", ",", ui.DARKGREEN, ui.GREEN,
        [
            "Les arbres parlent à voix basse. Ils parlent de toi.",
            "Une branche se penche comme un cou penché.",
            "Tu reconnais une voix dans l'écorce. Elle dit ton nom.",
            "Le sol respire sous la mousse.",
        ],
        [
            "« Les âmes qui ne peuvent plus partir prennent racine. La forêt est un cimetière qui pousse. »",
            "« La Mère des Racines fut une déesse mineure. Elle a oublié qu'elle n'était pas un arbre. »",
        ],
        "lyra", (3, 9),
    ),
    Region(
        "skaar", "Le Royaume Gelé de Skäar", "SKÄAR",
        "un temps arrêté, des consciences figées dans la glace",
        ent.MonsterDef("Le Gardien de l'Hiver", "H", ui.CYAN, 125, 16, 110, 3, 3, (), True),
        [
            ent.MonsterDef("Statue de glace hurlante", "i", ui.CYAN, 34, 11, 18, 3, 3),
            ent.MonsterDef("Chevalier figé", "k", ui.BLUE, 40, 13, 22, 3, 3, ()),
            ent.MonsterDef("Suppliant gelé", "s", ui.WHITE, 28, 12, 16, 3, 3, ("drain",)),
        ],
        "▓", "·", ui.BLUE, ui.CYAN,
        [
            "Le givre dessine des visages sur les murs.",
            "Un habitant te regarde. Ses yeux bougent encore.",
            "Tu entends « tuons-le » venir de trois statues à la fois.",
            "Il neige à l'intérieur.",
        ],
        [
            "« Skäar a arrêté son temps pour ne pas mourir. Ses habitants paient chaque seconde. »",
            "« Le Gardien combat depuis trois cents ans contre un ennemi qui n'existe plus. »",
        ],
        "morvan", (20, 1),
    ),
    Region(
        "necropole", "La Nécropole des Rois", "NÉCROPOLE",
        "une civilisation de morts avec ses lois, ses armées, ses rois",
        ent.MonsterDef("L'Empereur des Mille Âmes", "E", ui.PURPLE, 140, 17, 130, 4, 4, ("drain",), True),
        [
            ent.MonsterDef("Seigneur mort", "r", ui.BONE, 38, 13, 20, 4, 4, ("undead",)),
            ent.MonsterDef("Législateur squelette", "l", ui.GREY, 34, 14, 20, 4, 4, ("undead",)),
            ent.MonsterDef("Collecteur d'âmes", "A", ui.PURPLE, 42, 15, 24, 4, 4, ("drain",)),
        ],
        "▓", "·", ui.MIDGREY, ui.BONE,
        [
            "Un héraut annonce une loi que personne n'écoute.",
            "Des gardes morts te saluent. Tu ne sais pas pourquoi.",
            "Un trône vide est entouré de mille autres trônes.",
            "L'air sent la cire et le protocole.",
        ],
        [
            "« Les morts ont fondé leur royaume pour ne pas oublier qu'ils furent des rois. »",
            "« L'Empereur contient mille âmes. Il vote en secret contre lui-même. »",
        ],
        "aureth", (33, 4), True,
    ),
    Region(
        "forges", "Les Forges du Premier Monde", "FORGES",
        "là où les dieux ont fabriqué les humains pour alimenter la machine",
        ent.MonsterDef("Le Forgeron Primordial", "F", ui.ORANGE, 155, 18, 145, 5, 5, (), True),
        [
            ent.MonsterDef("Automate divin", "A", ui.ORANGE, 45, 15, 26, 5, 5),
            ent.MonsterDef("Moule vivante", "o", ui.BROWN, 40, 14, 22, 5, 5, ("poison",)),
            ent.MonsterDef("Étincelle consciente", "e", ui.YELLOW, 30, 17, 24, 5, 5, ("fast",)),
        ],
        "▓", "=", ui.BROWN, ui.ORANGE,
        [
            "Les chaînes de montage tournent encore, à vide.",
            "Un moule à visage attend une âme qui ne vient plus.",
            "Le métal est chaud comme une peau.",
            "Une voix compte : « un milliard trois cent mille... »",
        ],
        [
            "« Les dieux ne nous ont pas créés par amour. Ils nous ont fabriqués pour alimenter L'Origine. »",
            "« Chaque visage sorti d'ici était une batterie consciente. »",
        ],
        "lyra", (33, 10), True,
    ),
    Region(
        "audela", "L'Au-delà des Dieux", "AU-DELÀ",
        "derrière la réalité, là où les souvenirs deviennent des lieux",
        ent.MonsterDef("L'Écho du Premier Silence", "Ω", ui.WHITE, 170, 19, 160, 6, 6, ("drain",), True),
        [
            ent.MonsterDef("Lieu-souvenir", "L", ui.PURPLE, 46, 16, 28, 6, 6, ("drain",)),
            ent.MonsterDef("Passé qui marche", "P", ui.CYAN, 44, 17, 26, 6, 6, ()),
            ent.MonsterDef("Futur inversé", "U", ui.MAGENTA, 48, 18, 30, 6, 6, ("fast",)),
        ],
        "░", " ", ui.PURPLE, ui.MIDGREY,
        [
            "Le sol se souvient d'avoir été un ciel.",
            "Tu croises ton propre dos, qui s'éloigne.",
            "Une ville entière tient dans une flaque.",
            "Ici, mourir est un lieu-dit.",
        ],
        [
            "« Les dieux n'ont pas créé L'Origine. Ils l'ont trouvée. »",
            "« Le Premier Silence dormait dans le vide avant eux. Ils en ont pris un fragment. »",
        ],
        "lyra", (19, 14),
    ),
]

REGION_BY_KEY = {r.key: r for r in REGIONS}

# ------------------------------------------------------------------ PNJ
NPCS = {
    "kael": {
        "name": "KAEL, le chevalier sans mort",
        "glyph": "K", "color": ui.GOLD,
        "lines": [
            "« Je t'ai cherché pendant trois cents ans. »",
            "« Tu as arrêté la machine. Tu as condamné le monde. »",
            "Il lève son épée. Elle est ébréchée par trois siècles d'usage.",
        ],
    },
    "lyra": {
        "name": "LYRA, l'enfant qui se souvient",
        "glyph": "y", "color": ui.CYAN,
        "lines": [
            "Une fillette morte depuis des siècles te regarde sans peur.",
            "« Tu es en retard. Tu dis toujours ça, avant. »",
            "« Je me souviens de toutes tes morts. Tu veux que je te raconte ? »",
        ],
    },
    "morvan": {
        "name": "MORVAN, le marchand des âmes",
        "glyph": "M", "color": ui.GOLD,
        "lines": [
            "« Ah. Le revenant. » Il sourit avec trop de dents.",
            "« Je ne vends pas contre de l'or. L'or ne vaut rien chez les morts. »",
            "« Je prends des souvenirs. Trois, et tu repars avec quelque chose d'utile. »",
        ],
    },
    "aureth": {
        "name": "AURETH, le dieu déchu",
        "glyph": "A", "color": ui.YELLOW,
        "lines": [
            "Une silhouette assise sur un trône brisé lève la tête.",
            "« Le dernier des dieux vivants, oui. Enfin, vivant... »",
            "« Je peux te donner de la force. Il faudra me la rendre, un jour. »",
        ],
    },
}

# ---------------------------------------------------------------- textes
AMBUSH_WHISPERS = [
    "[Une voix dans le vide]  « Encore toi. »",
    "[Une voix dans le vide]  « Chaque mort t'approche de moi. »",
    "[Une voix dans le vide]  « Tu n'es pas immortel. La mort ne sait pas quoi faire de toi. »",
    "[Une voix dans le vide]  « Je me rapproche. »",
]

DEATH_TIERS = {
    1: "Une âme quitte ton corps. Tu la sens partir, soulagée.",
    2: "Les vivants commencent à te reconnaître. Ce n'est pas une bonne nouvelle.",
    3: "Des ennemis porteront désormais ton ancien équipement.",
    5: "Ton reflet s'est détaché. Il marche maintenant sans toi.",
    10: "Le Premier Silence te parle directement. Il n'a plus besoin de murs.",
}

LEGACY = {
    "sacrifice": {
        "title": "L'héritage du Sacrifice",
        "text": [
            "Tu es mort en détruisant Nhal'Zor. Le monde t'a fait martyr.",
            "Les cloches sacrées sonnent encore en ton nom : elles te protègent.",
        ],
        "bonus": {"max_hp": 8, "atk": 0, "souvenirs": 0},
    },
    "dieu": {
        "title": "L'héritage du Nouveau Dieu",
        "text": [
            "Tu as pris le trône du Néant. Les prêtres te haïssent,",
            "et leurs serviteurs morts te reconnaissent comme leur roi.",
        ],
        "bonus": {"max_hp": 0, "atk": 2, "souvenirs": 2},
    },
    "trahison": {
        "title": "L'héritage de la Trahison",
        "text": [
            "Tu as libéré Nhal'Zor. Ses serviteurs t'évitent encore,",
            "et certains te laissent passer sans combattre.",
        ],
        "bonus": {"max_hp": 4, "atk": 1, "souvenirs": 1},
    },
    "verite": {
        "title": "L'héritage de la Vérité",
        "text": [
            "Tu savais déjà ce que tu étais. Les inscriptions te reviennent",
            "plus vite que la lumière, et les morts te parlent comme à un frère.",
        ],
        "bonus": {"max_hp": 2, "atk": 1, "souvenirs": 3},
    },
    "secret": {
        "title": "L'héritage du Cycle Brisé",
        "text": [
            "Tu as brisé le cycle. Le monde ne t'attendait plus,",
            "mais rien n'a été prévu pour un revenant sans cycle.",
        ],
        "bonus": {"max_hp": 6, "atk": 2, "souvenirs": 2},
    },
    "aucun": {
        "title": "L'héritage de l'Oubli",
        "text": [
            "Aucune fin du Chapitre I n'est enregistrée. Le monde t'a oublié,",
            "et tu reviens sans passé. C'est peut-être une chance.",
        ],
        "bonus": {"max_hp": 5, "atk": 1, "souvenirs": 1},
    },
}

ENDING_CHOICES = [
    ("1", "dernier_dieu", "Le Dernier Dieu — prendre le contrôle de L'Origine"),
    ("2", "silence", "Le Grand Silence — libérer le Premier Silence"),
    ("3", "aube", "La Dernière Aube — détruire L'Origine et rendre la mort"),
    ("4", "sacrifice_eternel", "Le Sacrifice Éternel — devenir le cœur de la machine"),
    ("5", "verite_interdite", "La Vérité Interdite — refuser le choix et voir derrière"),
]

ENDINGS = {
    "dernier_dieu": {
        "title": "LE DERNIER DIEU",
        "colour": ui.PURPLE,
        "lines": [
            "Tu poses la main sur le cœur vivant de L'Origine.",
            "Mille visages hurlent, puis se taisent, puis t'obéissent.",
            "",
            "Tu deviens la loi. Les âmes ne s'accumulent plus :",
            "elles montent, dociles, vers le trône que tu viens d'inventer.",
            "",
            "Les survivants apprennent un nouveau nom à prier.",
            "Ils ne sauront jamais qu'ils prient un homme qui ne respire plus.",
        ],
    },
    "silence": {
        "title": "LE GRAND SILENCE",
        "colour": ui.WHITE,
        "lines": [
            "Tu ouvres. Pas une porte — une absence.",
            "",
            "Le Premier Silence récupère ce que les dieux lui ont volé.",
            "Les âmes, les villes, les ciels, les noms : tout retourne au rien.",
            "",
            "Il n'y a pas de cri. Il n'y a pas de fin du monde.",
            "Il n'y a plus de monde du tout.",
            "",
            "Quelque part, très loin, une voix murmure :",
            "« Merci d'avoir compris. »",
        ],
    },
    "aube": {
        "title": "LA DERNIÈRE AUBE",
        "colour": ui.GOLD,
        "lines": [
            "Tu brises L'Origine. Vraiment. Pas comme Nhal'Zor,",
            "qui voulait seulement la posséder.",
            "",
            "Les âmes prisonnières s'élèvent enfin et se dissolvent.",
            "Les morts cessent de marcher. Les cloches se taisent,",
            "parce qu'on n'a plus besoin d'elles.",
            "",
            "Un soleil gris se lève sur un monde vraiment vide —",
            "et pour la première fois depuis mille ans, il se couchera.",
            "Derrière toi, quelqu'un respire. C'est toi.",
        ],
    },
    "sacrifice_eternel": {
        "title": "LE SACRIFICE ÉTERNEL",
        "colour": ui.CYAN,
        "lines": [
            "Tu t'allonges dans la machine. Les visages se penchent.",
            "",
            "Tu deviens le nouveau cœur : ni dieu, ni mort, une pompe",
            "qui bat pour que les autres puissent vivre.",
            "",
            "Le monde survit. Les âmes circulent. Les cloches se taisent",
            "une heure par jour, pour te laisser dormir.",
            "",
            "Au-dessus de toi, les saisons reviennent lentement.",
            "Tu ne les verras pas. Tu les sens passer, comme un pouls.",
        ],
    },
    "verite_interdite": {
        "title": "LA VÉRITÉ INTERDITE",
        "colour": ui.MAGENTA,
        "lines": [
            "Tu regardes L'Origine et tu refuses de choisir.",
            "Tu regardes les âmes, les dieux, le Silence — et tu refuses.",
            "",
            "Alors tu vois ce qu'il y a derrière : une paroi fine,",
            "des caractères qui bougent, une lumière qui n'est pas la tienne.",
            "",
            "Le monde n'est pas une prison pour les hommes.",
            "C'est une prison pour quelqu'un d'autre,",
            "et quelqu'un la lit pendant que tu la traverses.",
            "",
            "Tu lèves la tête vers le ciel et tu dis :",
            "« Je te vois. »",
        ],
    },
}

FINAL_SCENE = [
    "L'écran devient noir. Plus de musique. Plus de texte.",
    "",
    "Puis quelques lignes apparaissent.",
    "",
    "          THE LAST BREATH — CHAPTER II",
    "",
    "Vous avez traversé les royaumes.",
    "Vous avez tué les anciens dieux.",
    "Vous avez défié la mort.",
    "",
    "Mais une dernière chose vous échappe.",
    "",
    "Qui vous a donné la possibilité de revenir ?",
    "",
    "Une voix inconnue répond :",
    "",
    "« Je ne suis pas Nhal'Zor. »",
    "« Je ne suis pas le Premier Silence. »",
    "« Je suis celui qui vous regarde depuis le début. »",
    "",
    "« Et maintenant... j'aimerais que tu sortes de cette prison. »",
]

CREATOR_UNLOCK = [
    "[UN NOUVEAU SOUVENIR A ÉTÉ DÉBLOQUÉ]",
    "",
    "Nom      : LE CRÉATEUR",
    "Statut   : INCONNU",
    "Origine  : INCONNUE",
    "Dernière apparition : ???",
]