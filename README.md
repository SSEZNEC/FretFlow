# FretFlow — Coach de guitare

> Pas seulement *quand* jouer — **comment** jouer.

## Philosophie

Chaque fonctionnalité doit aider le guitariste à progresser.
FretFlow indique la **position des doigts**, le **doigté**, les **accords**,
et propose des exercices ciblés.

## Milestone Coach (post-M6)

- Manche synchronisé (`FretboardWidget`)
- Moteur de doigté (`FingeringEngine`)
- Analyse d'accords + diagrammes
- Analyse pédagogique à l'import
- Mode Learn (tempo réduit, anticipation)
- Coach : passages difficiles → boucle + doigté

## Installation

Voir [INSTALL.md](INSTALL.md).

```bash
pip install -e ".[dev,import,ui,audio]"
fretflow ui
fretflow practise --auto
fretflow analyse-song morceau.gp5
```
