# Installation FretFlow

## Prérequis

- Python 3.12 ou plus récent
- Git (optionnel)
- Linux : `sudo apt install portaudio19-dev` pour le micro
- Windows / macOS : PortAudio via pip wheel (souvent inclus)

## Installation développement

```bash
git clone https://github.com/SSEZNEC/FretFlow.git
cd FretFlow
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
# .venv\Scripts\activate

pip install -e ".[dev,import,ui,audio]"
pytest
```

## Lancement

```bash
fretflow              # aide
fretflow ui           # interface graphique
fretflow practice --auto
fretflow progress
fretflow coach
fretflow export stats.json
```

## Emballage (optionnel)

```bash
pip install pyinstaller
pyinstaller --name FretFlow --windowed -m fretflow
```

Les données utilisateur restent locales :
- Linux : `~/.local/share/FretFlow/`
- Windows : `%LOCALAPPDATA%\SSEZNEC\FretFlow\`
- macOS : `~/Library/Application Support/FretFlow/`

## Accessibilité

- Thème sombre à fort contraste
- Raccourcis clavier (Espace, A–K)
- Textes de rapport en français clair
- Pas de dépendance réseau pour les fonctions essentielles
