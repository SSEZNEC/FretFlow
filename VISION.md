# FretFlow — Vision produit

## Mission

FretFlow est un compagnon d'apprentissage de la guitare open source. Il aide les guitaristes à progresser en jouant les morceaux qu'ils aiment, avec un retour clair, ludique et constructif.

Le projet s'inspire de l'accessibilité de Guitar Hero, de l'utilisation d'une vraie guitare popularisée par Rocksmith et de l'approche pédagogique de Yousician. Il ne cherche toutefois pas à les cloner : la progression musicale de l'utilisateur est la priorité, bien avant le score.

> Joue les morceaux que tu aimes. Progresse sans t'en rendre compte.

## Problème traité

Beaucoup de guitaristes savent qu'ils devraient travailler lentement, isoler les passages difficiles, pratiquer régulièrement et mesurer leurs progrès. Dans la pratique, il est difficile de savoir quoi travailler, comment évaluer une erreur et comment rester motivé.

FretFlow transforme chaque séance en une boucle utile : jouer, comprendre, pratiquer, mesurer, puis recevoir une recommandation pour la prochaine séance.

## Principes produit

1. **Pédagogie avant gamification.** Le score et les combos servent à motiver, mais ne doivent jamais masquer une faiblesse technique ou rythmique.
2. **Jouer de vrais morceaux.** L'utilisateur doit pouvoir importer ses partitions et construire une bibliothèque personnelle.
3. **Feedback bienveillant et actionnable.** Le logiciel explique ce qui peut être amélioré et propose une action concrète, sans punir ni décourager.
4. **Progression visible.** Les progrès par technique, morceau, section et période doivent être faciles à comprendre.
5. **Respect du joueur.** FretFlow fonctionne localement autant que possible, ne dépend pas d'un abonnement et garde les données de pratique sous le contrôle de l'utilisateur.
6. **Simplicité progressive.** Un débutant peut démarrer avec un morceau et un mode guidé ; les outils avancés restent disponibles sans encombrer l'expérience de base.

## Expérience cible

À l'ouverture, FretFlow accueille le joueur avec une recommandation courte : une séance réaliste selon son objectif, son historique et le temps disponible. Il peut ensuite choisir de jouer un morceau, travailler une boucle, faire un exercice ciblé ou consulter sa progression.

Pendant le jeu, l'interface reste lisible : rythme, notes attendues, résultat de la dernière action et indication utile. Après la séance, un rapport présente la précision rythmique, les passages fragiles et les techniques à consolider. Le coach peut proposer une boucle à vitesse réduite, un exercice de changement d'accords ou le retour au morceau complet.

## Modes principaux

### Jouer

Un affichage de type "highway" permet de jouer une partition avec une vraie guitare. Les notes défilent, les résultats de timing sont affichés et une session est enregistrée.

### Entraînement

Le joueur peut isoler une section, la mettre en boucle, ralentir ou accélérer le tempo, activer un métronome et faire augmenter automatiquement la vitesse après plusieurs réussites.

### Coach

Le coach transforme les résultats de session en recommandations. Il doit détecter les tendances utiles : retard rythmique constant, accord ou transition lente, passage difficile, manque de régularité, intonation de bend insuffisante, etc.

### Progression

Le tableau de bord montre l'évolution du temps de pratique, du rythme, des accords, du jeu lead et des techniques. Ces indicateurs sont des estimations transparentes basées sur des données observables, pas des jugements absolus.

### Bibliothèque

La bibliothèque indexe les morceaux importés et expose leurs métadonnées : titre, artiste, tempo, durée, accordage, pistes, techniques détectées, difficulté estimée et historique de pratique.

## Périmètre initial

La première version utilisable doit permettre de :

- importer des fichiers Guitar Pro (au minimum GP3, GP4 et GP5) et MIDI ;
- afficher les informations d'un morceau et une timeline jouable ;
- pratiquer des sections à vitesse réduite ;
- enregistrer une session et produire un rapport simple ;
- gérer un profil local et une bibliothèque SQLite ;
- préparer l'intégration de la détection audio, avec une voie de test clavier ou MIDI fiable.

## Hors périmètre initial

- réseau social, classement en ligne et multijoueur ;
- reconnaissance parfaite de toutes les techniques de guitare dès la première version ;
- transcription automatique d'audio commercial ;
- distribution de partitions ou d'enregistrements protégés par le droit d'auteur ;
- dépendance à une IA distante pour les fonctions essentielles.

## Critère de décision

Avant d'ajouter une fonctionnalité, poser cette question :

> Cette fonctionnalité aide-t-elle réellement un guitariste à progresser avec plaisir ?

Si la réponse n'est pas clairement oui, elle ne doit pas être prioritaire.
