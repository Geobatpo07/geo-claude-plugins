# solutions-claude-plugins

Marketplace **Claude Code** de skills personnalisés pour **Power BI / Microsoft Fabric**.

Ce dépôt **complète** [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) sans le modifier :

- les skills Microsoft (`fabric-skills`, `powerbi-authoring`) s'installent depuis la source officielle et se mettent à jour automatiquement ;
- nos règles maison (conventions, modélisation, DAX, design…) vivent ici, dans notre propre marketplace `geo-collection`.

> Les contenus marqués **« À ADAPTER »** sont des bonnes pratiques par défaut à remplacer par les règles réelles de l'équipe.

---

## Contenu

| Plugin | Skill | Rôle |
|---|---|---|
| `geo-powerbi` | `powerbi-conventions` | Nommage, organisation du modèle, règles DAX de base, processus de validation avant modification |
| | `powerbi-data-modeling` | Modélisation dimensionnelle : schéma en étoile, grain, clés, SCD, dimensions de rôle, tables pont |
| | `powerbi-tmdl` | Lecture/écriture de modèles sémantiques au format TMDL (projets PBIP) |
| | `powerbi-dax-library` | Bibliothèque de mesures standard (time intelligence, marges, parts, classements…) |
| | `powerbi-performance` | Optimisation DAX et modèle (cardinalité, VertiPaq, Power Query, diagnostic) |
| | `powerbi-report-design` | Charte des rapports : thème, mise en page, accessibilité, choix des visuels |
| | `powerbi-html-visuals` | Visuels HTML/SVG générés en DAX (tableaux, cartes, sparklines, barres de progression) |

Modèle pour créer un nouveau skill : [`templates/skill-template/`](templates/skill-template/).

## Structure

```
solutions-claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # catalogue des plugins (marketplace « geo-collection »)
├── plugins/
│   └── geo-powerbi/
│       ├── .claude-plugin/
│       │   └── plugin.json       # manifeste du plugin (version !)
│       └── skills/
│           └── <nom-du-skill>/
│               ├── SKILL.md      # instructions + frontmatter name/description
│               └── references/   # détails chargés à la demande
├── templates/skill-template/     # squelette à copier
├── scripts/validate.mjs          # contrôle de cohérence avant chaque push
├── CLAUDE.md / AGENTS.md         # règles pour éditer ce dépôt avec un agent
└── CHANGELOG.md
```

Différence avec le dépôt Microsoft : ici **pas de génération automatique**. Chaque skill n'existe qu'à un seul endroit (`plugins/<plugin>/skills/`) et `marketplace.json` est édité à la main.

## Installation (Claude Code)

Prérequis : Claude Code, Azure CLI connecté (`az login --allow-no-subscriptions`), plugins Microsoft installés.

```powershell
# 1. Plugins Microsoft (source officielle)
claude plugin marketplace add microsoft/skills-for-fabric
claude plugin install fabric-skills@fabric-collection
claude plugin install powerbi-authoring@fabric-collection

# 2. Nos skills
claude plugin marketplace add Geobatpo07/solutions-claude-plugins
claude plugin install geo-powerbi@geo-collection
```

Test local, avant de pousser sur GitHub :

```powershell
claude plugin marketplace add "C:\Users\gblaguerre\Documents\Data Analytics Projects\solutions-claude-plugins"
claude plugin install geo-powerbi@geo-collection
```

Activer la mise à jour automatique : dans Claude Code, `/plugin` → **Marketplaces** → `geo-collection` → **Enable auto-update** (idem pour `fabric-collection`).

## Ajouter ou modifier un skill

1. Copier `templates/skill-template/` vers `plugins/geo-powerbi/skills/<nouveau-nom>/`.
2. Renseigner `name` (identique au nom du dossier, en kebab-case) et `description` (quand l'utiliser — c'est ce qui déclenche le skill).
3. Garder `SKILL.md` court (< 300 lignes) ; déplacer les détails dans `references/`.
4. **Incrémenter la version** dans `plugins/geo-powerbi/.claude-plugin/plugin.json` **et** `.claude-plugin/marketplace.json` (mêmes valeurs).
5. Ajouter une entrée dans `CHANGELOG.md`.
6. Valider puis publier :

```powershell
npm run validate
git add .
git commit -m "feat(powerbi): <résumé>"
git push
```

Sans incrément de version, Claude Code ne voit pas la mise à jour.

## Coexistence avec les skills Microsoft

| Besoin | Skill Microsoft | Notre skill (appliqué en plus) |
|---|---|---|
| Modifier un modèle sémantique | `semantic-model-authoring` | `powerbi-conventions`, `powerbi-data-modeling`, `powerbi-tmdl` |
| Écrire des mesures | `semantic-model-authoring` | `powerbi-dax-library`, `powerbi-performance` |
| Créer / modifier un rapport | `powerbi-report-cli` | `powerbi-report-design`, `powerbi-html-visuals` |
| Questions en langage naturel sur les données | `fabriciq` | — |

Les skills Microsoft gèrent la **mécanique** (API Fabric, fichiers PBIR/PBIP, MCP) ; les nôtres imposent les **règles maison**. En cas de contradiction, nos conventions priment sur les choix de style, jamais sur les contraintes techniques des API.
