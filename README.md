# FretFlow

**Coach d\'apprentissage de la guitare open source.**

> Joue les morceaux que tu aimes. Progresse sans t\'en rendre compte.

## Version 0.1.0 — Milestone 6 (finition 1.0)

Fonctionnel de bout en bout :

1. Importer un morceau (MIDI / Guitar Pro)
2. Pratiquer (CLI ou UI highway)
3. Analyser la seance (coach)
4. Suivre sa progression (dashboard / export)

## Installation

Voir [INSTALL.md](INSTALL.md).

```bash
pip install -e ".[dev,import,ui,audio]"
fretflow ui
```

## Commandes

| Commande | Description |
|----------|-------------|
| `fretflow ui` | Interface graphique |
| `fretflow practice --auto` | Seance demo + coach |
| `fretflow coach` | Skills et objectifs |
| `fretflow progress` | Resume de progression |
| `fretflow export stats.json` | Export JSON/CSV |
| `fretflow scan <dossier>` | Indexer des partitions |
| `fretflow library` | Lister la bibliotheque |

## Architecture

```
core/ engine/ audio/ input/ importers/
library/ practice/ coach/ profile/ ui/
```

Documentation produit : VISION.md, ARCHITECTURE.md, ROADMAP.md.
