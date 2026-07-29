# FretFlow

**Coach d'apprentissage de la guitare open source.**

## État actuel

**Milestone 4 — Audio et calibration** ✅

- Détecteur de hauteur monophonique (autocorrélation + rejet sous-harmoniques)
- Buffer circulaire, pipeline audio → notes validées
- Capture simulée (tests) + sounddevice (optionnel, si PortAudio)
- Calibration de latence, validation/debounce
- CLI `diagnose-audio` et `devices`

Milestones 0–3 inclus (import, bibliothèque, session, UI highway).

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,import,ui,audio]"
# Linux : sudo apt install portaudio19-dev   # pour le micro réel
pytest
```

## Commandes

```bash
fretflow ui
fretflow practice --auto
fretflow diagnose-audio --freq 440
fretflow devices
fretflow scan ~/Partitions
```
