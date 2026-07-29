# FretFlow — Feuille de route

## Principes de planification

Chaque jalon produit une application exécutable et testée. Les jalons ne sont pas des promesses de calendrier : ils décrivent un ordre de dépendances et une définition claire de "terminé".

La priorité est une boucle d'apprentissage utile : importer un morceau, travailler une section, obtenir un retour et suivre son évolution. Les effets visuels et les fonctions sociales viennent après cette base.

## Milestone 0 — Socle développeur

**But :** disposer d'un dépôt installable et cohérent.

- `pyproject.toml`, verrouillage ou stratégie de dépendances, outillage Ruff et pytest ;
- package `fretflow`, point d'entrée et configuration TOML ;
- journalisation structurée et répertoires de données utilisateur ;
- modèles métier minimaux ;
- CI qui exécute formatage, lint, typage et tests ;
- documentation de démarrage.

**Terminé lorsque :** `python -m fretflow` ou la commande équivalente démarre une application minimale sur une installation propre.

## Milestone 1 — Bibliothèque et import Guitar Pro

**But :** importer et comprendre les morceaux de l'utilisateur.

- import GP3, GP4, GP5 via PyGuitarPro ;
- import MIDI initial via Mido ;
- conversion vers `Song`, mesures, temps, pistes, notes, tempo, signatures et techniques disponibles ;
- scanner configurable d'un dossier de morceaux ;
- index SQLite et fiche de morceau ;
- fichiers de test de référence : *Highway to Hell* et *Simple Man* fournis par l'utilisateur ;
- vue de bibliothèque simple et écran de détails.

**Terminé lorsque :** les fichiers de référence apparaissent dans la bibliothèque avec des métadonnées correctes et une timeline inspectable.

## Milestone 2 — Session et pratique manuelle

**But :** rendre possible une séance réellement utile, même sans détection audio parfaite.

- profil local, création de session et historique ;
- sélection de piste, section et difficulté ;
- timeline, playhead, pause, seek, vitesse 50–100 % ;
- boucle A/B et métronome ;
- contrôles clavier et/ou MIDI pour le test ;
- rapport de session minimal : durée, notes attendues, timing, réussites et erreurs.

**Terminé lorsque :** un utilisateur peut travailler une section en boucle à tempo réduit et retrouver la session dans son historique.

## Milestone 3 — Affichage de jeu et jugement

**But :** créer une boucle de jeu motivante et fiable.

- écran de jeu PySide6, highway lisible et notes synchronisées au temps de jeu ;
- curseur de partition efficace ;
- fenêtres Perfect / Great / Good / Miss configurables ;
- score, combo, précision et résultats ;
- support des notes simples et des notes longues ;
- événements de session structurés et tests de timing.

**Terminé lorsque :** une session clavier/MIDI peut être jouée de bout en bout avec un résultat cohérent, quel que soit le FPS.

## Milestone 4 — Audio et calibration

**But :** utiliser une vraie guitare comme entrée.

- capture audio robuste et sélection de périphérique ;
- buffer circulaire, prétraitement, détecteur de hauteur interchangeable ;
- validation de note, seuil de bruit et outils de diagnostic ;
- calibration de latence et profil d'accordage ;
- comparaison initiale hauteur + timing pour les notes monophoniques ;
- mode de simulation pour les tests et dépannage.

**Terminé lorsque :** une note de guitare correctement jouée peut être reconnue de manière stable sur un matériel courant, avec une procédure de calibration claire.

## Milestone 5 — Analyse et coach

**But :** transformer les sessions en conseils concrets.

- `PerformanceReport` détaillé ;
- analyse par mesure, section, technique et offset rythmique ;
- détection de passages difficiles ;
- recommandations explicables ;
- génération d'exercices de boucle et progression automatique de tempo ;
- objectifs quotidiens et hebdomadaires simples.

**Terminé lorsque :** après un morceau, FretFlow peut recommander une section précise et une méthode de travail justifiée par les résultats.

## Milestone 6 — Progression et finition 1.0

**But :** fournir une première version quotidienne, durable et distribuable.

- dashboard, graphiques de progression et carnet de pratique ;
- sauvegarde/migrations robustes ;
- thèmes sombre et accessibilité de base ;
- emballage Windows et documentation d'installation ;
- export CSV/JSON des statistiques ;
- couverture de test des parcours critiques et guide de contribution.

**Terminé lorsque :** un nouvel utilisateur peut installer FretFlow, importer un morceau, pratiquer, analyser sa séance et retrouver ses progrès sans intervention technique.

## Après 1.0

- reconnaissance élargie des accords, bends, slides, vibrato et palm mute ;
- éditeur de partition/exercice ;
- support de contrôleurs supplémentaires ;
- plugins d'import et de pédagogie ;
- synchronisation optionnelle et chiffrée des profils ;
- partage de packs d'exercices, sans distribution de contenu protégé ;
- fonctions de coaching local avancées, uniquement si elles restent explicables et respectueuses de la confidentialité.

## Non-objectifs de roadmap

La roadmap ne fixe pas de dates arbitraires. Une fonctionnalité reste expérimentale tant qu'elle n'est pas mesurable, testable et utile à l'apprentissage réel.
