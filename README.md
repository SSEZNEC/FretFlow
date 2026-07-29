# FretFlow — Professeur de guitare

> Écoute. Pose les doigts. Joue. Progresse.

## Milestone Professeur (Reference Audio + Ear Training)

Le logiciel enseigne **quand**, **où**, **comment** et **quel son** obtenir.

### Nouveautés

- **ReferenceAudioEngine** — prévisualisation sonore (sons de guitare synthétisés)
- Modes : OFF / NOTE / ACCORD / TEMPO / LEARN / SILENCIEUX (sur erreur)
- **Ear training** — `fretflow ear-train`
- **Call & response** — phrases à reproduire
- Banque de timbres : clean, acoustic, crunch, jazz, classical
- Bibliothèque d'accords ouverts + diagrammes
- Manche + doigté (M7) toujours présents

### Installation

Voir [INSTALL.md](INSTALL.md).

```bash
pip install -e ".[dev,import,ui,audio]"
fretflow ui
fretflow ear-train --count 5
fretflow practice --auto
```
