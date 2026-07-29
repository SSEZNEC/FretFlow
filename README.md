# FretFlow

**Coach d'apprentissage de la guitare open source.**

> Joue les morceaux que tu aimes. Progresse sans t'en rendre compte.

## État actuel

**Milestone 3 — Affichage de jeu et jugement** ✅

- Highway PySide6 synchronisé au temps de jeu
- Notes simples et longues, score / combo / précision
- Contrôles clavier (A–K) + play/pause (Espace)
- Tempo 50–100 %, bibliothèque graphique
- Session runner + rapport (M2) branchés sur l'UI

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,import,ui]"
pytest
```

## Lancer l'interface

```bash
fretflow ui
```

Dans la fenêtre :
1. **Démo C majeur** pour un essai immédiat
2. **Importer** un `.mid` / `.gp5` ou **Scanner** un dossier
3. **Jouer** — les notes défilent vers la ligne de hit
4. Touches **A S D F G H J K** = notes ; **Espace** = pause

## CLI (sans UI)

```bash
fretflow scan ~/Partitions
fretflow library
fretflow practice --auto
fretflow history
```

## Architecture UI

L'UI ne calcule ni score ni DSP : elle appelle `SessionRunner` et affiche l'état.

```
ui/
├── main_window.py    # bibliothèque + lancement
├── game_window.py    # session + contrôles
├── highway_widget.py # rendu highway (paintEvent)
└── colors.py         # thème sombre
```
