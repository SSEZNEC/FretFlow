# FretFlow

**Coach d'apprentissage de la guitare open source.**

> Joue les morceaux que tu aimes. Progresse sans t'en rendre compte.

## État actuel

**Milestone 2 — Session et pratique manuelle** ✅

- Import MIDI + Guitar Pro, bibliothèque SQLite
- Horloge de jeu (play/pause/seek/tempo 25–200 %)
- Jugement Perfect / Great / Good / Miss
- Boucle A/B, section, métronome (scheduler)
- Session runner + rapport + historique SQLite
- CLI `practice --auto` pour démonstration sans micro

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,import]"
pytest
```

## Commandes

```bash
fretflow scan ~/Partitions
fretflow library
fretflow import morceau.mid
fretflow practice --auto                  # démo C majeur
fretflow practice --auto --tempo 0.7 fichier.mid
fretflow practice --auto --start 10 --end 20 --loop fichier.mid
fretflow history
```

## Architecture

```
fretflow/
├── core/        # modèles, config
├── importers/   # GP + MIDI
├── library/     # SQLite morceaux
├── engine/      # horloge, jugement, session runner
├── practice/    # boucle, métronome, settings
├── profile/     # sessions & profil local
├── input/       # clavier (test)
└── app.py       # CLI
```

Voir VISION.md, ARCHITECTURE.md, ROADMAP.md.
