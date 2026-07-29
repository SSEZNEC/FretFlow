# FretFlow

Coach d\'apprentissage de la guitare open source.

## Etat actuel

**Milestone 5 — Analyse et coach** OK

- SessionReport riche (outcomes, sections)
- Detection de faiblesses explicables
- Recommandations → exercices concrets + plan
- SkillProfile persiste (SQLite)
- Objectifs quotidiens / hebdomadaires
- CLI `practice` et `coach`

## Installation

```bash
pip install -e ".[dev,import,ui,audio]"
pytest
```

## Commandes

```bash
fretflow practice --auto
fretflow coach
fretflow ui
```
