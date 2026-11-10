"""Menu principal : Chapitre I / Chapitre II."""
from __future__ import annotations

from . import lore, ui

BOX_W = 74


def _box(title: str, body: list[str], footer: str, colour: int) -> list[str]:
    inner = BOX_W - 2
    lines = ["╔" + "═" * inner + "╗"]
    lines.append("║" + ui.pad(ui.paint(title, colour, bold=True), inner, "center") + "║")
    lines.append("╠" + "═" * inner + "╣")
    for row in body:
        if not row:
            lines.append("║ " + " " * (inner - 2) + " ║")
            continue
        if "\x1b" in row or len(row) <= inner - 2:
            chunks = [row]
        else:
            chunks = ui.wrap(row, inner - 2)
        for chunk in chunks:
            lines.append("║ " + ui.pad(chunk, inner - 2) + " ║")
    lines.append("╠" + "═" * inner + "╣")
    lines.append("║ " + ui.pad(ui.paint(footer, ui.GREY), inner - 2) + " ║")
    lines.append("╚" + "═" * inner + "╝")
    return ["", ""] + lines


def main_menu(term, mem) -> str | None:
    ch2 = mem.ch2
    ch3 = mem.ch3
    while True:
        endings1 = len(mem.endings)
        body = [
            ui.paint("Trois chapitres. Une seule mort qui ne finit pas.", ui.MIDGREY),
            "",
            ui.paint("[1]  CHAPITRE I — LES ÉCHOS DU DERNIER SOUFFLE", ui.GOLD, bold=True),
            f"     7 étages, Nhal'Zor, 5 fins   ·   fins trouvées : {endings1}/5"
            f"   ·   cycles : {mem.cycle}",
            "",
            ui.paint("[2]  CHAPITRE II — LE ROYAUME DES ÂMES BRISÉES", ui.MAGENTA, bold=True),
            "     6 régions, le Premier Silence, 5 fins"
            f"   ·   âmes perdues : {ch2['deaths']}",
            "",
            ui.paint("[3]  CHAPITRE III — THE GOD BEHIND THE SCREEN", ui.WHITE, bold=True),
            "     5 territoires, THE AUTHOR, 6 fins"
            f"   ·   souvenirs : {len(ch3['memories'])}/7",
        ]
        if ch3["endings"]:
            body.append(ui.paint(f"     fins du chapitre III : {len(ch3['endings'])}/6", ui.CYAN))
        if ch3.get("ch4_teaser"):
            body.append(ui.paint("     [A NEW STORY IS BEING WRITTEN]", ui.PURPLE))
        if ch2["endings"]:
            body.append(ui.paint(f"     fins du chapitre II : {len(ch2['endings'])}/5", ui.CYAN))
        if ch2.get("ch3_teaser"):
            body.append(ui.paint("     [UN SOUVENIR ATTEND : LE CRÉATEUR]", ui.PURPLE))
        body += ["", ui.paint("─" * 64, ui.DARKGREY)]
        if mem.endings:
            body.append(ui.paint(f"Héritage du Chapitre I : {lore.ENDING_JOURNAL.get(mem.endings[-1], '')}",
                                 ui.BONE))
        else:
            body.append(ui.paint("Aucune fin du Chapitre I enregistrée : le Chapitre II commencera",
                                 ui.MIDGREY))
            body.append(ui.paint("avec l'héritage de l'Oubli.", ui.MIDGREY))
        body += ["",
                 ui.paint("Prompts : GPT   ·   Code : DeepSeek V4.1 Flash   ·   [C] crédits",
                          ui.DARKGREY),
                 ui.paint("[R] effacer toute la mémoire   [Q] quitter", ui.MIDGREY)]
        term.clear()
        term.draw(_box(lore.TITLE + "  ·  THE LAST BREATH", body,
                       "Choisis ton chapitre.", ui.GOLD))
        key = term.getkey().lower()
        if key in ("1", "enter", "space", " "):
            return "ch1"
        if key == "2":
            return "ch2"
        if key == "3":
            return "ch3"
        if key == "c":
            term.clear()
            term.draw(_box("CRÉDITS", [
                ui.paint("CYCLE DES CENDRES — THE LAST BREATH", ui.GOLD, bold=True),
                "",
                "Projet vibecoding : direction humaine, IA outillée.",
                "",
                ui.paint("Prompts de design", ui.CYAN, bold=True),
                "  rédigés avec GPT — univers, chapitres, mécaniques,",
                "  contraintes de fiabilité (Prompt/Gpt_prompt.txt).",
                "",
                ui.paint("Code", ui.CYAN, bold=True),
                "  cuisiné avec DeepSeek V4.1 Flash via l'agent Hermes",
                "  (Nous Research) : 3 chapitres, familier autonome,",
                "  système d'objets anti-duplication, 183 tests.",
                "",
                ui.paint("Humain", ui.CYAN, bold=True),
                "  arbitrages, ton, difficulté, validation en terminal.",
                "",
                "Détail : CREDITS.md dans le dépôt.",
            ], "[ESC] retour", ui.GOLD))
            term.getkey()
            continue
        if key == "r":
            term.clear()
            term.draw(["", "", "  " + ui.paint("Effacer TOUTE la mémoire (chapitres I et II) ? (o/n)",
                                               ui.RED, bold=True)])
            if term.getkey().lower() in ("o", "y"):
                mem.reset()
        if key in ("q", "esc"):
            return None