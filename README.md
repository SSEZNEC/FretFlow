# FretFlow

**Coach d'apprentissage de la guitare open source.**

> Joue les morceaux que tu aimes. Progresse sans t'en rendre compte.

Voir [VISION.md](VISION.md) pour la mission produit et [ARCHITECTURE.md](ARCHITECTURE.md) pour l'architecture technique.

## État actuel

**Milestone 1 — Bibliothèque et import** ✅

- Package Python installable (`fretflow`)
- Modèles métier (`Song`, `Track`, `Measure`, `Note`, `Session`…)
- Import **MIDI** (Mido) et **Guitar Pro** GP3/GP4/GP5 (PyGuitarPro)
- Scanner de dossiers + index **SQLite** local
- CLI : `scan`, `import`, `library`
- Configuration TOML, journalisation, tests

Prochaines étapes : Milestone 2 — session de pratique manuelle (boucle, tempo, métronome).

## Prérequis

- Python 3.12+
- Git

## Installation (développement)

```bash
git clone https://github.com/SSEZNEC/FretFlow.git
cd FretFlow
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,import]"
```

## Lancer

```bash
fretflow                          # statut
fretflow --version
fretflow --init-config            # écrire la config par défaut

# Bibliothèque
fretflow scan ~/Partitions        # importer un dossier (récursif)
fretflow scan ~/Partitions --force
fretflow import morceau.mid       # un seul fichier
fretflow import morceau.gp5
fretflow library                  # lister les morceaux indexés
```

## Tests

```bash
pytest
ruff check .
ruff format --check .
```

## Architecture (résumé)

```
fretflow/
├── core/        # Modèles, config, erreurs (aucune dépendance UI/audio)
├── importers/   # Guitar Pro + MIDI → Song
├── library/     # Scanner + SQLite
├── engine/      # (M2+) horloge, jugement
├── audio/ input/ practice/ coach/ profile/ ui/
└── app.py       # CLI + composition root
```

Le noyau métier ne dépend ni de Qt, ni de `sounddevice`, ni de PyGuitarPro.

## Documentation

| Document | Contenu |
|----------|---------|
| [VISION.md](VISION.md) | Mission et principes produit |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architecture et règles de dépendance |
| [ROADMAP.md](ROADMAP.md) | Jalons |
| [STYLE_GUIDE.md](STYLE_GUIDE.md) | Conventions de code |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guide de contribution |
| [AI_INSTRUCTIONS.md](AI_INSTRUCTIONS.md) | Règles pour les assistants IA |

## Licence

MIT (à confirmer).
