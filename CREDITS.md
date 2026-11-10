# Crédits — comment ce jeu a été fait

**CYCLE DES CENDRES / THE LAST BREATH** est un projet *vibecoding* : la direction
créative est humaine, la rédaction des cahiers des charges et l'écriture du code
sont assistées par des modèles de langage.

## 1. Les prompts — GPT

Les cahiers des charges (univers, chapitres, mécaniques, système d'objets,
familier autonome, contraintes de fiabilité) ont été rédigés avec **GPT**.
Le prompt d'origine du Chapitre I est conservé tel quel dans le dépôt :

```
Prompt/Gpt_prompt.txt   (≈ 2 850 lignes : scénario, monstres, objets, fins)
```

Chaque chapitre a été spécifié de la même façon : un document de design en
français, avec des règles explicites (« aucune duplication d'objets », « aucun
vol de butin », « ne pas casser les sauvegardes ») qui servent ensuite de
critères d'acceptation.

## 2. Le code — DeepSeek V4.1 Flash

L'implémentation a été **cuisinée avec DeepSeek V4.1 Flash**, piloté via
l'agent **Hermes (Nous Research)** : lecture de l'architecture existante,
création des modules, intégration aux trois chapitres, puis correction des bugs
observés en exécution réelle.

Ce qui a été fait par le modèle :

- `game/ui.py`, `dungeon.py`, `entities.py`, `items.py`, `memory.py`, `menu.py`
- les trois chapitres : `game.py`, `chapter2.py`, `chapter3.py` (+ `lore*.py`)
- le système d'objets fiable : `item_db.py`, `item_manager.py`, `loot_manager.py`
- le familier autonome : `familiar.py`, `familiar_ai.py`, `familiar_field.py`
- les suites de tests : `tests/test_game.py`, `test_chapter2.py`,
  `test_chapter3.py`, `test_familiar.py`

## 3. Ce qui reste humain

- les décisions de design (ton, difficulté, ce qui est « drôle » ou « sinistre ») ;
- les arbitrages : 40 objets utiles plutôt que 300 inutiles, deux inventaires
  strictement séparés, pas de familier qui joue à la place du joueur ;
- la validation : chaque fonctionnalité est vérifiée en vrai terminal, et les
  chiffres annoncés sortent des tests (`183` vérifications au total).

## 4. Méthode

1. un prompt de design en français (GPT) ;
2. une passe d'implémentation (DeepSeek V4.1 Flash) ;
3. exécution réelle : tests headless, parties scriptées, rendu du cadre 79×28 ;
4. correction des bugs constatés — jamais des bugs supposés.

Aucune dépendance externe : uniquement la bibliothèque standard Python.
Le jeu est jouable dans un terminal Windows (UTF-8 / ANSI), et les sources sont
intégralement lisibles dans ce dépôt.

---

*« Death is not the end. It is only the beginning of something worse. »*
