# Changelog

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) — versionnement [SemVer](https://semver.org/lang/fr/).

## [1.1.0] — 2026-10-13

Inspiré du guide « How I Build Power BI Reports with AI » (L. Reese).

### Ajouté
- Skill `powerbi-mockup` : maquette HTML d'une page à partir du modèle réel (champs étiquetés, mesures manquantes listées, itérations, passage au PBIP) avec gabarit et checklist.
- `powerbi-report-design` : quatre questions par page, jetons de design chiffrés, structure en Z avec interrupteurs, vérification visuelle par capture, revue « 5 problèmes », fonds de page SVG (`fonds-svg.md`), boucle de références visuelles (`references/visuels/`, modèle d'entrée et première référence « carte KPI avec comparaison »).
- `powerbi-dax-library` : interrupteurs par tables déconnectées (Plan / N-1, Haut / Bas, Mensuel / Cumul), titres et couleurs dynamiques.
- `powerbi-conventions` : règles « modèle existant vs nouveau modèle », confidentialité des métadonnées (données de santé / personnelles), commentaire QUOI / COMMENT / ADAPTER dans les mesures, Git obligatoire avant écriture.

### Modifié
- `powerbi-conventions` : précision `DIVIDE(a, b, 0)` ≠ `COALESCE(DIVIDE(a, b), 0)`.
- `powerbi-tmdl` : synchronisation avec Desktop (enregistrer avant, appliquer les changements externes ou Desktop Bridge) au lieu de « fermer Desktop ».

## [Non publié] — 2026-10-13

### Ajouté
- `scripts/bump-versions.mjs` : incrémente automatiquement la version d'un plugin modifié (niveau déduit des messages de commit).
- `scripts/generate-marketplace.mjs` (`npm run generate`, option `--check`) : génère la liste `plugins` de `marketplace.json` depuis les `plugin.json`.
- Workflow GitHub Actions `generate-marketplace.yml` (webhook `push` sur `main`) : régénère et commit `marketplace.json` automatiquement.

## [1.0.0] — 2026-10-13

### Ajouté
- Marketplace `geo-collection` et plugin `geo-powerbi`.
- Skills : `powerbi-conventions`, `powerbi-data-modeling`, `powerbi-tmdl`, `powerbi-dax-library`, `powerbi-performance`, `powerbi-report-design`, `powerbi-html-visuals`.
- Modèle de skill (`templates/skill-template/`) et script `scripts/validate.mjs`.
