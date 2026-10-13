# Changelog

Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) — versionnement [SemVer](https://semver.org/lang/fr/).

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
