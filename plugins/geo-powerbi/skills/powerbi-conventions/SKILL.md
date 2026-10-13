---
name: powerbi-conventions
description: "Conventions maison pour Power BI : nommage des tables, colonnes et mesures, dossiers d'affichage, descriptions, formats, organisation du modèle et processus de validation avant toute modification. À charger AVANT de créer ou modifier un modèle sémantique, une mesure DAX, une relation ou un rapport Power BI, en complément de semantic-model-authoring et powerbi-report-cli. Triggers: convention, nommage, naming, standard, mesure, measure, table, colonne, modèle sémantique, semantic model, Power BI."
---

# Conventions Power BI

> Valeurs par défaut fondées sur les bonnes pratiques reconnues. Les sections marquées **À ADAPTER** doivent être remplacées par les règles validées de l'équipe.

Ce skill fait foi pour le **style**. Les skills Microsoft (`semantic-model-authoring`, `powerbi-report-cli`) font foi pour la **mécanique** (API, fichiers, MCP). Les skills `powerbi-data-modeling`, `powerbi-dax-library`, `powerbi-performance`, `powerbi-tmdl`, `powerbi-report-design` et `powerbi-html-visuals` appliquent ces conventions.

## Processus obligatoire avant toute modification

1. **Inventorier** l'existant : tables, colonnes, mesures, relations, rôles RLS concernés.
2. **Détecter** les écarts aux conventions ci-dessous et les signaler (sans les corriger d'office).
3. **Proposer un plan** : liste des objets créés / modifiés / supprimés, impact sur les rapports.
4. **Attendre la validation explicite** de l'utilisateur pour toute suppression, tout renommage (casse les visuels et les références) et toute modification de relation.
5. **Exécuter**, puis **vérifier** (requête DAX de contrôle, valeurs attendues).
6. **Résumer** les changements dans un tableau objet / action / raison.

Ne jamais travailler directement sur un modèle de **production** : passer par l'espace de travail de développement ou une copie PBIP.
Avant toute écriture : le projet doit être sous **Git** avec un arbre propre (commit de sauvegarde), pour que chaque modification soit réversible.

## Modèle existant vs nouveau modèle

Les conventions de nommage s'appliquent **pleinement aux nouveaux modèles**. Sur un modèle **existant** (déjà publié, déjà utilisé) :

- **Ne pas proposer de renommer les tables** (préfixes `Fact_` / `Dim_`…) sauf demande explicite : gain faible, risque élevé pour les rapports, les signets et les rapports connectés au modèle publié.
- Avant de renommer une **mesure ou une colonne**, faire l'**inventaire des champs utilisés** par le rapport (`*.Report/`) et par les autres rapports connectés ; présenter l'impact.
- Prioriser les corrections **sans impact visuel** : table de dates, `summarizeBy`, masquage, formats, descriptions, dossiers d'affichage.
- Signaler les écarts de nommage dans l'audit, en **priorité basse**.

## Nommage — À ADAPTER

| Objet | Règle | Exemples |
|---|---|---|
| Table de faits | `Fact_` + processus métier au pluriel | `Fact_Ventes`, `Fact_Stocks` |
| Dimension | `Dim_` + entité au singulier | `Dim_Client`, `Dim_Produit`, `Dim_Date` |
| Table de mesures | `_Mesures` (tri en tête de liste) | `_Mesures` |
| Table de paramètres / groupes de calcul | `Param_` / `CG_` | `Param_Indicateur`, `CG_Temps` |
| Colonne visible | Libellé métier en français, espaces autorisés, sans abréviation | `Nom client`, `Date de commande` |
| Colonne technique (clé, tri, flag) | PascalCase anglais, **masquée** | `CustomerKey`, `MonthSortOrder` |
| Mesure | Libellé métier, unité ou nature en suffixe si ambigu | `CA HT`, `Marge brute %`, `Nb clients` |
| Mesure intermédiaire | Préfixe `_`, **masquée** | `_CA Base` |
| Variable DAX | `_` + camelCase | `_caN1`, `_dateMax` |

Règles générales :

- Pas d'accents ni d'espaces dans les **noms de tables** (simplifie DAX, M et TMDL) ; accents autorisés dans les colonnes et mesures visibles.
- Pas de nom identique entre une mesure et une colonne.
- Toujours référencer une colonne avec sa table (`Fact_Ventes[Montant]`) et une mesure **sans** table (`[CA HT]`).

## Organisation du modèle

- Toutes les mesures dans `_Mesures` (ou dans la table de faits correspondante si le modèle est grand — **À ADAPTER**), rangées en **dossiers d'affichage** : `01 Ventes`, `02 Marge`, `03 Clients`, `90 Technique`.
- Masquer : clés, colonnes de tri, colonnes déjà agrégées par une mesure, tables de faits brutes si tout passe par des mesures.
- `Summarize by` = **None** pour toutes les colonnes numériques non additives (identifiants, années, taux).
- Désactiver **Date/heure automatique** ; utiliser `Dim_Date` marquée comme table de dates.
- Chaque colonne de tri (`Nom du mois`) a son **Sort by column** défini.

## Descriptions et formats

- **Toute mesure visible a une description** : définition métier, règle de calcul, source. Elle apparaît en info-bulle dans le volet Données.
- Les mesures non triviales commencent par un **commentaire en trois lignes** :

```dax
// QUOI : CA HT de la période comparé à N-1, en %.
// COMMENT : (N - N-1) / N-1 ; BLANK si pas de N.
// ADAPTER : remplacer [CA HT] par la mesure de base.
```
- Formats : montants `#,##0 €` (**À ADAPTER** : devise HTG / USD / EUR), pourcentages `0.0 %`, entiers `#,##0`, dates `dd/MM/yyyy`.
- Préférer des **chaînes de format dynamiques** aux mesures `FORMAT()` (qui renvoient du texte et cassent le tri et les totaux).

## Règles DAX minimales

- `DIVIDE(a, b)` au lieu de `a / b`. Attention : `DIVIDE(a, b, 0)` n'équivaut **pas** à `COALESCE(DIVIDE(a, b), 0)` — le 3ᵉ argument ne s'applique que si le dénominateur est nul ou vide ; si le numérateur est vide, `DIVIDE` renvoie BLANK. Ne pas remplacer l'un par l'autre sans vérifier l'intention. Préférer BLANK à 0 (voir `powerbi-performance`).
- Variables (`VAR … RETURN`) dès qu'une expression est réutilisée ou pour la lisibilité.
- Filtres de colonne dans `CALCULATE` plutôt que `FILTER(Table, …)` sur une table entière.
- Pas d'`IFERROR` / `ISERROR` : traiter le cas en amont.
- Une mesure = une idée ; composer les mesures (`[Marge brute] = [CA HT] - [Coût]`).
- Formatage : une fonction par ligne au-delà de ~80 caractères, indentation 4 espaces (style DAX Formatter).

Détails et exemples : [references/checklist-revue.md](references/checklist-revue.md).

## Sécurité et gouvernance

### Confidentialité des métadonnées

Un projet PBIP ne contient pas les lignes de données, mais ses **métadonnées** sont envoyées au fournisseur d'IA dès qu'un agent les lit : noms de tables, colonnes, mesures et pages, logique DAX, titres, descriptions, rôles RLS (qui peuvent contenir des e-mails ou des noms), paramètres et chaînes de connexion.

- **Avant d'ouvrir un projet réel avec un agent**, vérifier que l'outil est autorisé par l'organisation pour ce type de données — **impératif pour les données de santé ou personnelles**.
- Préférer un **projet d'exemple** ou anonymisé pour expérimenter.
- Ne jamais lire ni transmettre `.pbi/cache.abf` (données chargées) ni `.pbi/localSettings.json` ; vérifier qu'ils sont dans `.gitignore`.
- Signaler à l'utilisateur, sans les recopier, les e-mails, noms de personnes ou secrets trouvés dans les rôles, paramètres ou expressions M.

### Règles

- RLS : rôles nommés `RLS_<périmètre>` (`RLS_Region`), filtres sur les dimensions, jamais sur les faits ; tester avec « Afficher en tant que ».
- Ne jamais écrire d'identifiants, mots de passe ou chaînes de connexion en clair dans le modèle ou les paramètres.
- Étiquette de sensibilité obligatoire avant publication — **À ADAPTER**.
