# FretFlow — Architecture

## Objectifs techniques

L'architecture doit permettre une application de bureau stable, testable et évolutive. Le noyau métier ne doit dépendre ni de Qt, ni d'une bibliothèque audio, ni d'un format de partition particulier. Les interfaces utilisateur et matérielles sont des adaptateurs autour de ce noyau.

Principes :

- dépendances orientées vers le domaine ;
- composition et injection de dépendances ;
- modules à responsabilité unique ;
- modèles de données explicites et typés ;
- données utilisateur locales et portables ;
- tests unitaires indépendants de l'interface et du microphone.

## Vue d'ensemble

```text
PySide6 UI ───────────────┐
Audio / MIDI / clavier ───┼──> Application / services ──> Noyau métier
Importeurs de morceaux ───┤             │                       │
SQLite / fichiers locaux ─┘             └──> événements / sessions / coach
```

Le noyau gère les modèles de morceau, les sessions, le jugement, les statistiques et les recommandations. Les adaptateurs gèrent les détails de Qt, `sounddevice`, PyGuitarPro, Mido et SQLite.

## Organisation proposée

```text
FretFlow/
├── fretflow/                 # Package applicatif
│   ├── app.py                # Composition root et cycle de vie
│   ├── core/                 # Modèles, événements, configuration, erreurs
│   ├── engine/               # Horloge, timeline, jugement, session de jeu
│   ├── audio/                # Capture, DSP, détection, validation, calibration
│   ├── input/                # Adaptateurs clavier, MIDI, microphone, replay
│   ├── importers/            # Guitar Pro, MIDI, JSON interne
│   ├── library/              # Scanner et persistance des morceaux
│   ├── practice/             # Boucles, tempo, métronome, pratique adaptative
│   ├── coach/                # Analyse, recommandations, exercices
│   ├── profile/              # Profils, objectifs, sessions, statistiques
│   └── ui/                   # Fenêtres et widgets PySide6
├── tests/
├── docs/
├── assets/
├── examples/
├── pyproject.toml
└── README.md
```

## Couches et règles de dépendance

### `core`

Contient les objets métier et les contrats communs : `Song`, `Track`, `Measure`, `Note`, `Technique`, `Session`, `PerformanceReport`, événements et exceptions. Cette couche n'importe que la bibliothèque standard et, si nécessaire, des dépendances légères de validation.

Les données sont généralement des `@dataclass(slots=True)`. Les identifiants, timestamps et unités sont explicites : secondes pour le temps interne, millisecondes pour les offsets affichés, MIDI pour les hauteurs.

### `engine`

Gère la logique déterministe de jeu et de pratique : horloge, curseur de partition, fenêtres de jugement, score, combo et génération d'événements. Il ne dessine rien et n'ouvre aucun périphérique.

L'horloge de jeu doit pouvoir être mise en pause, cherchée et ralentie. À terme, elle peut être synchronisée sur une horloge audio ; l'API métier ne doit pas changer.

### `audio` et `input`

`audio` encapsule la capture et le traitement numérique : buffer circulaire, prétraitement, détection de hauteur, validation temporelle et calibration. `input` transforme les résultats matériels en événements métier tels que `PlayedNote` ou `StrumEvent`.

Le moteur reçoit uniquement les événements normalisés. Il ne connaît pas `sounddevice`, ASIO, WASAPI ou une API de manette.

La détection audio doit rester interchangeable : un protocole de détecteur permet d'utiliser YIN, MPM ou un détecteur simulé pour les tests.

### `importers` et `library`

Chaque importeur convertit un format externe vers le modèle interne `Song`. Les importeurs ne calculent ni score ni rendu. `library` indexe ensuite les métadonnées et analyses dans SQLite afin d'éviter de reparcourir chaque fichier à chaque lancement.

### `practice` et `coach`

`practice` contient les outils contrôlés par l'utilisateur : boucle, tempo, métronome, sélection de section. `coach` analyse une session terminée, identifie des difficultés et génère des recommandations. Les recommandations doivent pouvoir être expliquées par les données observées.

### `profile`

Persiste les profils, objectifs, sessions et agrégats de progression. Les données de session doivent rester assez riches pour permettre de recalculer des statistiques plus tard, sans conserver d'audio brut par défaut.

### `ui`

La couche PySide6 traduit l'état applicatif en interface. Elle appelle les cas d'usage et écoute les événements ; elle ne contient ni calcul DSP, ni règles de score, ni accès SQL direct.

## Composition root

`fretflow.app.Application` est le seul endroit qui construit les services concrets. Il charge la configuration, initialise la base de données, crée les adaptateurs d'entrée, compose le moteur et démarre la fenêtre. Les autres modules reçoivent leurs dépendances au constructeur.

## Persistance

- **TOML** pour les préférences et paramètres explicites de l'utilisateur.
- **SQLite** pour la bibliothèque, les profils, les sessions, les objectifs et les statistiques agrégées.
- **JSON** uniquement pour les exports, le format d'échange interne ou les snapshots lisibles.

Les migrations de schéma doivent être versionnées. Les chemins utilisateur doivent utiliser `platformdirs` ou un équivalent, jamais un chemin absolu codé en dur.

## Événements

Un bus d'événements léger peut découpler les consommateurs d'un résultat de jeu : l'interface, le rapport de session, le stockage et le replay peuvent écouter un `HitEvent` sans s'appeler directement. Le bus est synchrone par défaut ; les opérations longues sont déléguées à une file ou un worker explicite.

## Tests

- modèles, jugement, score, boucle et coach : tests unitaires purs ;
- importeurs : fixtures GP3/MIDI compactes et tests de conversion ;
- base de données : SQLite temporaire ;
- audio : signaux NumPy synthétiques, jamais un microphone réel en CI ;
- UI : tests `pytest-qt` pour les parcours critiques seulement.

## Sécurité et confidentialité

FretFlow doit être local-first. Ne pas envoyer de données de pratique, fichiers musicaux ou enregistrements audio sans consentement explicite. Ne jamais inclure de clés, mots de passe ou contenus protégés dans le dépôt.
