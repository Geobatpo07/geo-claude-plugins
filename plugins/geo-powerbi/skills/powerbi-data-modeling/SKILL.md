---
name: powerbi-data-modeling
description: "Modélisation de données dimensionnelle pour Power BI et Fabric : conception de schéma en étoile, choix du grain, tables de faits et dimensions, clés de substitution, dimensions à évolution lente (SCD), dimensions de rôle, tables pont plusieurs-à-plusieurs, table de dates, choix Import / DirectQuery / Direct Lake. À utiliser pour concevoir, critiquer ou refondre un modèle sémantique, ou transformer des tables sources en modèle analytique. Triggers: modélisation, data modeling, star schema, schéma en étoile, fait, dimension, grain, relation, cardinalité, SCD, many-to-many, snowflake, Kimball."
---

# Modélisation de données — Power BI

Appliquer aussi `powerbi-conventions` (nommage, validation). Pour écrire les changements dans un projet PBIP, utiliser `powerbi-tmdl` ; pour les publier, `semantic-model-authoring`.

## Démarche de conception (Kimball, 4 étapes)

1. **Processus métier** : quel événement mesure-t-on ? (vente, commande, stock journalier, ticket support).
2. **Grain** : que représente **une ligne** de la table de faits ? L'écrire en une phrase (« une ligne = une ligne de facture »). Ne jamais mélanger deux grains dans une même table.
3. **Dimensions** : qui, quoi, où, quand, comment ? Chaque dimension décrit le contexte du fait au grain choisi.
4. **Faits** : mesures numériques cohérentes avec le grain (additives, semi-additives comme les soldes, non additives comme les taux → à recalculer en mesure DAX, jamais stockées).

Livrer la conception sous forme de tableau **table / type / grain / clé / relations** et d'un diagramme (Mermaid `erDiagram`) avant de modifier quoi que ce soit.

## Règles

- **Schéma en étoile** : dimensions reliées directement aux faits, relations **1 → \*** (dimension → fait), **filtrage unidirectionnel**.
- **Pas de flocon** : dénormaliser les hiérarchies (Produit → Sous-catégorie → Catégorie) dans une seule `Dim_Produit`.
- **Pas de relation fait ↔ fait.** Deux faits partagent des **dimensions conformes** (`Dim_Date`, `Dim_Produit`).
- **Clés** : entiers de substitution (`ProductKey`) côté modèle ; garder la clé métier en colonne d'attribut. Une ligne « Inconnu » (clé −1) par dimension pour les faits orphelins.
- **Table de dates** : une `Dim_Date` continue (du 1er janvier de la première année au 31 décembre de la dernière), une ligne par jour, marquée comme table de dates. Voir [references/dim-date.md](references/dim-date.md).
- **Colonnes** : ne charger que les colonnes utiles ; séparer date et heure ; arrondir les décimales inutiles.
- **Mesures plutôt que colonnes calculées** pour tout ce qui s'agrège.
- Transformations en amont (source, Lakehouse/Warehouse, Power Query) plutôt qu'en DAX.

## Cas particuliers

| Situation | Solution | Détails |
|---|---|---|
| Plusieurs dates sur un fait (commande, livraison) | Dimension de rôle : une relation active + relations inactives activées par `USERELATIONSHIP` | [patterns](references/patterns.md#dimensions-de-rôle) |
| Historique des attributs (région du client qui change) | SCD type 2 : clé de substitution par version + `DateDébut` / `DateFin` / `EstCourant` | [patterns](references/patterns.md#scd) |
| Plusieurs-à-plusieurs (client ↔ comptes) | Table pont + filtrage contrôlé | [patterns](references/patterns.md#plusieurs-à-plusieurs) |
| Faits à des grains différents (budget mensuel vs ventes journalières) | Tables de faits séparées, relation au niveau commun (mois) via colonne de la dimension | [patterns](references/patterns.md#grains-différents) |
| En-tête / détail (commande / lignes) | Aplatir l'en-tête dans la table des lignes ; répartir les montants d'en-tête si nécessaire | [patterns](references/patterns.md#en-tête-détail) |
| Petits attributs disparates (flags) | Dimension « junk » ou attributs dégénérés dans le fait | [patterns](references/patterns.md#dimensions-junk-et-dégénérées) |

## Mode de stockage

| Mode | Quand | Points d'attention |
|---|---|---|
| **Import** | Par défaut ; volumes jusqu'à quelques centaines de millions de lignes | Planifier l'actualisation ; actualisation incrémentielle sur les gros faits |
| **Direct Lake** (Fabric) | Données déjà en Delta dans un Lakehouse/Warehouse Fabric | Tables Delta optimisées (V-Order), pas de colonnes calculées ; repli DirectQuery possible |
| **DirectQuery** | Temps réel strict ou volumes impossibles à importer | Performances dépendantes de la source ; limiter les visuels ; agrégations |
| **Composite** | Mélange (faits en DirectQuery + dimensions en Dual) | Dimensions en mode **Dual** |

## Livrables attendus

1. Tableau de conception (tables, grain, clés, relations).
2. Diagramme Mermaid du modèle cible.
3. Liste des écarts entre l'existant et la cible, priorisés.
4. Plan de migration (ordre des changements, impacts rapports) — **validation utilisateur requise** avant exécution.
