# Contribuer à FretFlow

Merci de vouloir contribuer à FretFlow. Le projet vise un logiciel local, accessible et utile pour la pratique de la guitare. Chaque contribution doit préserver cette intention.

## Avant de commencer

1. Lire [VISION.md](VISION.md), [ARCHITECTURE.md](ARCHITECTURE.md) et [STYLE_GUIDE.md](STYLE_GUIDE.md).
2. Chercher une issue ou une discussion existante avant de commencer une fonctionnalité importante.
3. Pour une modification d'architecture, proposer d'abord une courte note de conception : problème, solution proposée, alternatives et impact sur les tests.

## Pré-requis

- Python 3.12 ou plus récent ;
- Git ;
- un environnement virtuel ;
- les dépendances de développement déclarées dans `pyproject.toml`.

Exemple de démarrage, à adapter aux outils choisis par le dépôt :

```bash
git clone https://github.com/SSEZNEC/FretFlow.git
cd FretFlow
python -m venv .venv
# Activer l'environnement, puis :
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

## Flux de contribution

1. Créer une branche courte et descriptive : `feature/gp3-library`, `fix/audio-device-error`, `docs/practice-mode`.
2. Garder une modification centrée sur un objectif unique.
3. Ajouter ou adapter les tests concernés.
4. Mettre à jour la documentation si l'API, le comportement utilisateur ou l'installation change.
5. Exécuter les contrôles locaux avant d'ouvrir une pull request.
6. Rédiger une pull request concise : contexte, solution, tests réalisés, limites éventuelles et captures pour les changements UI.

## Définition de terminé

Une contribution est prête lorsque :

- le code est lisible, typé et formaté ;
- les tests pertinents existent et passent ;
- les erreurs sont gérées avec un message exploitable ;
- elle ne crée pas de dépendance circulaire ni de couplage UI/métier ;
- elle ne stocke ni secret, ni donnée personnelle, ni contenu musical non autorisé ;
- elle apporte une valeur démontrable à l'apprentissage ou à la fiabilité du produit.

## Tests

Favoriser les tests déterministes.

- Pour l'audio, utiliser des signaux NumPy synthétiques et des adaptateurs simulés.
- Pour les importeurs, utiliser de petites fixtures autorisées ou générées ; ne pas committer d'œuvres protégées sans autorisation.
- Pour la base de données, utiliser une base SQLite temporaire.
- Pour l'UI, tester les parcours essentiels avec `pytest-qt`, sans dupliquer les tests métier.

Une correction de bug doit généralement inclure un test qui échouait avant la correction.

## Propositions de fonctionnalités

Pour proposer une nouvelle fonction, préciser :

- le besoin de l'utilisateur ;
- la manière de mesurer son utilité ;
- le flux utilisateur ;
- les données manipulées ou sauvegardées ;
- les effets sur la confidentialité ;
- le plan de test ;
- les alternatives envisagées.

Les fonctions de gamification, de réseau ou d'IA doivent être particulièrement justifiées : elles ne sont acceptées que si elles améliorent concrètement la pratique.

## Documentation

Utiliser le français pour les documents produit et une langue cohérente dans le code existant (anglais recommandé pour les identifiants, messages techniques et API). Les nouveaux concepts publics doivent être documentés près de leur module et, si nécessaire, dans `docs/`.

## Signalement de bugs

Inclure autant que possible :

- version de FretFlow, OS et version Python ;
- périphérique audio et pilote, si le problème est audio ;
- étapes de reproduction ;
- résultat attendu et résultat observé ;
- journal anonymisé ;
- fichier de partition minimal reproduisant le problème, si sa licence le permet.

Ne jamais publier de clés, identifiants, informations personnelles ou enregistrements privés.

## Code de conduite pratique

Être précis, respectueux et constructif. Les retours de revue portent sur le code et le comportement du produit, jamais sur la personne. L'objectif commun est un outil fiable qui donne envie de jouer davantage.
