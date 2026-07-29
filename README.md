# FretFlow

**Professeur de guitare open source — Beta 0.9**

> Apprenez plus vite. Jouez plus juste. Revenez chaque jour.

## Pour les guitaristes (sans Python)

1. Téléchargez **FretFlow.exe** depuis les Releases GitHub
2. Double-cliquez
3. **Importer un morceau** (MIDI ou Guitar Pro)
4. Cliquez **Pratiquer**

## Pour les développeurs

```bash
pip install -e ".[dev,import,ui,audio]"
pytest
fretflow ui
```

Build Windows :

```powershell
.\build.ps1
```

## Parcours utilisateur

```
Accueil → Bibliothèque → Morceau → Pratique (manche + tips)
       → Rapport du professeur → Tableau de bord → Revenir demain
```

## Documentation

- INSTALL.md — installation détaillée
- CHANGELOG.md — nouveautés
