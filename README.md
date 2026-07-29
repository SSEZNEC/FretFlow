# FretFlow — Votre professeur de guitare

> Un professeur particulier installé sur votre ordinateur.

## Version 1.0 — Virtual Guitar Teacher

Interface en **3 zones synchronisées** :

1. **Highway** — quand jouer  
2. **Manche** — où et comment (doigtés)  
3. **Teacher Panel** — conseils en temps réel  

### Capacités

- Tips live : « Prépare ton barré », « Excellent timing », « Attention au slide »
- Dialogue de fin de séance (encourageant, jamais punitif)
- Plans d\'entraînement auto (échauffement → accords → morceau → technique → retour au calme)
- Reference audio (NOTE / LEARN / DEMO / ASSIST / CORRECTION)
- Feedback hauteur : ✔ / ▲ / ▼ / ≈
- Ear training, call & response
- Analyse pédagogique GP, progression, exports

### Installation

```bash
pip install -e ".[dev,import,ui,audio]"
fretflow ui
fretflow plan --minutes 45 --song "Mon morceau"
fretflow practice --auto
```

Voir [INSTALL.md](INSTALL.md).
