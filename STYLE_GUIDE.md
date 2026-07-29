# FretFlow — Guide de style et conventions

## Objectif

Le code FretFlow doit être facile à lire, modifier et tester plusieurs années après son écriture. La cohérence prime sur les préférences individuelles.

## Langue

- Les identifiants Python, noms de modules, API et messages techniques sont en anglais.
- La documentation produit et l'interface peuvent être en français, avec une stratégie de traduction prévue si nécessaire.
- Éviter les abréviations ambiguës : préférer `sample_rate` à `sr`, `current_time` à `t` hors contexte mathématique très local.

## Formatage et analyse statique

- Utiliser Ruff pour le lint et le formatage, configuré dans `pyproject.toml`.
- Longueur de ligne cible : 88 caractères, sauf configuration contraire du dépôt.
- Ne pas désactiver une règle de lint sans justification locale et précise.
- Les imports sont triés automatiquement et séparés : bibliothèque standard, dépendances tierces, package FretFlow.

## Modules et nommage

- Modules et fonctions : `snake_case`.
- Classes, exceptions et énumérations : `PascalCase`.
- Constantes : `UPPER_SNAKE_CASE`.
- Variables booléennes : `is_`, `has_`, `can_`, `should_` lorsque cela améliore la lecture.
- Les modules décrivent une responsabilité : `pitch_detector.py`, pas `helpers.py` ou `misc.py`.

## Typage

Annoter les paramètres et retours des fonctions publiques. Préférer les types concrets quand ils clarifient le contrat.

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(slots=True)
class SongReference:
    path: Path
    title: str

def scan_song_files(root: Path) -> list[SongReference]:
    ...
```

Éviter `Any` sauf aux frontières externes, puis convertir/valider immédiatement. Utiliser `Protocol` pour les dépendances interchangeables, par exemple un détecteur de hauteur ou une source d'horloge.

## Modèles de domaine

- Utiliser `@dataclass(slots=True)` pour les données métier simples.
- Utiliser `frozen=True` pour les valeurs réellement immuables (ex. profil de timing, référence de fichier).
- Ne pas stocker de logique UI ou I/O dans `Song`, `Note`, `Session` ou `PerformanceReport`.
- Les collections mutables doivent utiliser `field(default_factory=list)` ou équivalent.

## Temps et unités

Les unités sont une source importante d'erreurs dans un logiciel musical.

- Temps interne : `float` en secondes, suffixe facultatif `_seconds` si le contexte n'est pas évident.
- Offsets affichés : millisecondes, nommés `offset_ms`.
- Hauteur : MIDI entier et fréquence en Hz ; justesse en cents.
- Audio : échantillons entiers, fréquence en `sample_rate`.
- Tempo : BPM en `bpm`.

Ne jamais mélanger secondes et millisecondes dans une même API sans nom explicite.

## Erreurs et logs

- Lever des exceptions métier spécifiques aux frontières : import, configuration, périphérique audio, persistance.
- Ne pas utiliser `assert` pour valider une entrée utilisateur ou un fichier externe.
- Journaliser avec le logger de projet et un contexte utile.
- Éviter les logs au niveau `INFO` dans une boucle de frame ou un callback audio.

```python
logger.warning("Audio device reported an overflow: %s", status)
```

Ne jamais écrire de données sensibles, d'audio ou de contenu de partition complet dans les journaux.

## Conception des fonctions

- Une fonction doit faire une chose identifiable.
- Préférer les retours explicites aux modifications cachées d'état.
- Préférer les objets de paramètres lorsqu'une signature devient longue ou fragile.
- Éviter les méthodes qui à la fois lisent un fichier, calculent une analyse, écrivent en base et mettent à jour l'UI.

## UI

- L'UI PySide6 ne contient pas de règle métier.
- Les widgets appellent des cas d'usage et reçoivent des view models ou événements.
- Ne pas bloquer le thread UI avec de l'import, du DSP ou de la base de données longue durée.
- Fournir des états vides, de chargement et d'erreur clairs.
- Favoriser le contraste, la taille de texte et les raccourcis clavier accessibles.

## Audio

- Les callbacks doivent être courts et prévisibles.
- Préallouer autant que possible dans le chemin temps réel.
- Isoler NumPy/SciPy dans `audio` ; le domaine reçoit des résultats validés.
- Documenter les compromis entre latence, stabilité et précision.

## Base de données et fichiers

- Centraliser les chemins utilisateur.
- Utiliser des transactions pour les écritures multi-étapes.
- Versionner les migrations.
- Ne pas stocker un chemin de machine comme identifiant de morceau durable si un hash ou une référence portable est plus adaptée.

## Tests

Nommer les tests par comportement :

```python
def test_judge_returns_perfect_inside_perfect_window() -> None:
    ...
```

Chaque test doit préparer ses données, exécuter une action et vérifier un résultat clair. Éviter les tests qui dépendent de l'ordre, de l'heure système, d'un périphérique réel ou du réseau.

## Commits et pull requests

- Un commit ou une pull request = une intention principale.
- Préférer un titre à l'impératif : `Add GP3 song importer`.
- Inclure les tests avec le changement fonctionnel, pas dans une tâche ultérieure indéfinie.
- Mettre à jour la documentation lorsque l'utilisateur ou un développeur doit changer sa manière d'utiliser le projet.

## Critère final

Avant de finaliser un changement, se demander : est-il compréhensible sans connaître toute l'histoire du projet, testable sans matériel spécial et utile pour aider un guitariste à progresser ?
