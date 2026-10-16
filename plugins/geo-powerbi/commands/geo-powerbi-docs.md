---
description: Guide d'utilisation du plugin geo-powerbi (skills, commandes, script lean.py, méthode de travail). Argument optionnel : une section.
argument-hint: "[installation | skills | exemples | lean | dette | methode | securite | depannage]"
---

Présente à l'utilisateur le guide ci-dessous, en français, **sans rien exécuter ni modifier**.

- Si `$ARGUMENTS` est vide : affiche la section « Vue d'ensemble », puis la table des matières des sections et la façon d'en ouvrir une (`/geo-powerbi-docs <section>`).
- Si `$ARGUMENTS` correspond à une section (ou en est proche) : affiche uniquement cette section, en entier.
- Si `$ARGUMENTS` est une question (« comment auditer un modèle ? ») : réponds à partir de ce guide et indique la section concernée.
- Termine toujours par une ligne : « Version installée : » suivie du résultat de la commande `claude plugin list` pour `geo-powerbi` si tu peux la lire, sinon omets cette ligne.

---

# geo-powerbi — guide d'utilisation

## Vue d'ensemble

`geo-powerbi` ajoute à Claude Code des **règles et méthodes maison** pour Power BI. Il complète les skills Microsoft (`fabric-skills`, `powerbi-authoring`), qui gèrent la **mécanique** (fichiers PBIP, API Fabric, connexion à Power BI Desktop). Les skills se chargent **automatiquement** selon votre demande : il suffit d'écrire ce que vous voulez en français.

| Section | Contenu |
|---|---|
| `installation` | Prérequis et installation |
| `skills` | Les 9 skills et quand ils s'activent |
| `exemples` | Demandes prêtes à l'emploi |
| `lean` | Le script d'analyse `lean.py` |
| `dette` | `DETTE.md` et `MODIFICATIONS.md` |
| `methode` | La méthode de travail recommandée |
| `securite` | Données sensibles et garde-fous |
| `depannage` | Problèmes fréquents |

## installation

Prérequis sur le poste : **Azure CLI** (`az login --allow-no-subscriptions`), **Node.js LTS** (pour le serveur MCP Microsoft), **Python 3.8+** (pour `lean.py`), **Git** (avec `git config --global credential.helper manager`), **Claude Code**.

```powershell
# Skills Microsoft (mécanique PBIP / Fabric)
claude plugin marketplace add microsoft/skills-for-fabric
claude plugin install fabric-skills@fabric-collection
claude plugin install powerbi-authoring@fabric-collection

# Skills maison
claude plugin marketplace add Geobatpo07/geo-claude-plugins
claude plugin install geo-powerbi@geo-collection
```

Puis dans Claude Code : `/plugin` → **Marketplaces** → `geo-collection` et `fabric-collection` → **Enable auto-update**. Vérifier avec `/mcp` que `plugin:powerbi-authoring:powerbi-modeling-mcp` est connecté (sinon **Reconnect**).

Les rapports doivent être enregistrés au format **PBIP** (Power BI Desktop → Fichier → Enregistrer sous → *Fichiers projet Power BI*).

## skills

| Skill | S'active quand vous… |
|---|---|
| `powerbi-conventions` | modifiez un modèle ou un rapport ; auditez un modèle « selon nos conventions » (nommage, descriptions, formats, processus de validation, modèle existant, confidentialité) |
| `powerbi-data-modeling` | concevez ou refondez un modèle : schéma en étoile, grain, SCD, dimensions de rôle, table de dates |
| `powerbi-tmdl` | lisez ou modifiez les fichiers `.tmdl` d'un projet PBIP |
| `powerbi-dax-library` | écrivez des mesures : cumuls, N-1, ratios, classements, nouveaux clients, interrupteurs Plan / N-1 |
| `powerbi-performance` | une page ou une mesure est lente ; vous voulez optimiser DAX, modèle ou Power Query |
| `powerbi-mockup` | voulez une maquette HTML d'une page à partir du modèle réel, avant de construire |
| `powerbi-report-design` | concevez ou revoyez une page : quatre questions, grille, couleurs, fonds SVG, accessibilité |
| `powerbi-html-visuals` | voulez un visuel SVG / HTML en DAX (sparkline, barre de progression, carte KPI) |
| `powerbi-lean` | demandez une revue, un audit, l'inventaire d'un champ, l'état de la dette ou le journal des modifications |

Les valeurs marquées « À ADAPTER » dans les skills (préfixes, couleurs, devise…) sont des choix par défaut, pas des obligations.

## exemples

| Objectif | Demande à écrire |
|---|---|
| Découvrir un modèle | « Liste les tables, mesures et relations du modèle de ce projet. » |
| Auditer | « Audite le modèle selon nos conventions. » / « Lance un audit powerbi-lean. » |
| Avant un renommage | « Où est utilisée la mesure [Nom de la mesure] ? » |
| Corriger sans risque | « Applique les corrections sans impact visuel de l'audit (table de dates, summarizeBy, masquage). Montre-moi le plan avant. » |
| Nouvelle mesure | « Ajoute une mesure de cumul annuel et d'évolution vs N-1 pour [Mesure]. Montre-moi le DAX avant. » |
| Nouvelle page | « Fais une maquette HTML d'une page de suivi de [sujet] à partir du modèle. » |
| Lenteur | « Ce visuel met 30 s à charger : diagnostique avec powerbi-performance, sans rien modifier. » |
| Avant commit | « Fais une revue powerbi-lean de mes modifications. » |
| Dette | « Où en est la dette du projet ? » / « Solde D-004 : la correction est faite et vérifiée. » |

## lean

Script Python en **lecture seule**, fourni avec `powerbi-lean`. Claude le lance lui-même ; vous pouvez aussi l'exécuter :

```powershell
python "<dossier du skill>/scripts/lean.py" audit <projet>                 # audit complet
python "<dossier du skill>/scripts/lean.py" audit <projet> --changed       # fichiers modifiés depuis le dernier commit
python "<dossier du skill>/scripts/lean.py" usage <projet>                 # champs utilisés par page / visuel
python "<dossier du skill>/scripts/lean.py" usage <projet> --field "[Mesure]"
python "<dossier du skill>/scripts/lean.py" dette <projet>                 # état DETTE.md + MODIFICATIONS.md
```

`--json` donne une sortie exploitable. « Inutilisé » = non utilisé par **ce** rapport : vérifiez la vue de traçabilité de l'espace de travail avant de supprimer.

## dette

Deux fichiers à la racine de chaque projet, versionnés avec lui :

- `DETTE.md` : ce qui reste à corriger (`D-001`…), avec priorité et échéance.
- `MODIFICATIONS.md` : ce qui a été corrigé ou ajouté (`M-001`…), plus récent en haut ; il se remplit à mesure que la dette diminue.

Solder une dette : entrée `M-xxx` dans le journal → `D-xxx` déplacée dans « Soldé » avec `**Modification** : M-xxx` → `lean.py dette` sans incohérence → un commit `M-xxx: …`. Avancée partielle : `D-xxx (partielle)`. Projet existant sans journal : « Initialise MODIFICATIONS.md en reprenant l'historique Git ».

## methode

1. **Audit** en lecture seule.
2. **Plan** priorisé : d'abord ce qui ne change pas les visuels, les renommages en dernier.
3. **Commit de sauvegarde** ; Power BI Desktop enregistré.
4. **Maquette HTML** pour toute nouvelle page.
5. **Exécution** par étapes ; DAX montré avant application ; décisions métier laissées à l'utilisateur.
6. **Vérification** dans Desktop (valeurs avant / après) et revue humaine.
7. **Revue powerbi-lean**, journal, commit, push.

## securite

- Claude lit les **métadonnées** du projet (noms, DAX) : vérifiez que c'est autorisé pour le projet.
- Les **données** (`.pbi/cache.abf`) ne doivent jamais être lues ni versionnées : `.gitignore` + règle `deny Read(**/.pbi/cache.abf)` dans `~/.claude/settings.json`.
- Les requêtes DAX via le MCP renvoient de vraies données : à valider une par une (règle `ask`).
- Les maquettes n'utilisent que des valeurs fictives ; `DETTE.md` et `MODIFICATIONS.md` ne contiennent jamais de valeurs réelles.
- Dépôts privés uniquement ; pas de `git push` automatique.

## depannage

| Symptôme | Solution |
|---|---|
| Skills absents | `claude plugin list` ; `claude plugin update geo-powerbi@geo-collection` ; relancer `claude` |
| `powerbi-modeling-mcp` en × | `/mcp` → Reconnect ; si fréquent : `$env:MCP_TIMEOUT="60000"` avant `claude` |
| Écriture refusée par le mode auto | Projet sous Git + `.claude/settings.local.json`, ou mode par défaut (Shift+Tab) |
| `python` ouvre le Microsoft Store | `winget install Python.Python.3.12`, puis rouvrir le terminal |
| Changements non visibles dans Desktop | Appliquer les changements externes ou rouvrir le `.pbip` |
| Visuel très lent | « Diagnostique avec powerbi-performance » ; copier la requête de l'Analyseur de performances vers DAX Studio |

Contribuer (nouvelle règle, nouvelle référence visuelle) : voir le `README.md` du dépôt `Geobatpo07/geo-claude-plugins`.
