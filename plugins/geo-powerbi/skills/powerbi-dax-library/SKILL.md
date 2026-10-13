---
name: powerbi-dax-library
description: "Bibliothèque de mesures DAX standard : mesures de base, time intelligence (cumul annuel, N-1, évolution %, glissement 12 mois, moyenne mobile), marges, parts du total, classements, Top N, nouveaux clients, groupes de calcul, paramètres de champs et interrupteurs par tables déconnectées (Plan/N-1, Haut/Bas, Mensuel/Cumul). À utiliser pour écrire, compléter ou corriger des mesures DAX afin de réutiliser les modèles validés au lieu de réinventer les formules. Triggers: DAX, mesure, measure, YTD, cumul, N-1, YoY, évolution, variation, part, ratio, rang, RANKX, Top N, moyenne mobile, time intelligence, calculation group, switch, table déconnectée, disconnected table, SELECTEDVALUE, titre dynamique."
---

# Bibliothèque DAX

Appliquer `powerbi-conventions` (nommage, format, description) et `powerbi-performance` (patterns efficaces). Les modèles supposent un schéma en étoile avec `Dim_Date` marquée comme table de dates (voir `powerbi-data-modeling`).

## Méthode

1. **Chercher d'abord** dans le modèle une mesure existante qui fait déjà le calcul ; la réutiliser.
2. Partir d'une **mesure de base** (`[CA HT]`, `[Quantité]`, `[Nb clients]`) et composer.
3. Adapter le modèle de la bibliothèque : remplacer les noms génériques (`Fact_Ventes`, `Dim_Date`, `[Mesure]`) par ceux du modèle réel.
4. Ajouter description, format et dossier d'affichage.
5. **Tester** avec une requête de contrôle (voir ci-dessous) sur un périmètre dont on connaît le résultat.

## Catalogue

| Famille | Mesures | Référence |
|---|---|---|
| Base | Somme, nombre de lignes, distinct, moyenne pondérée | [base](references/mesures-base.md) |
| Temps | YTD, QTD, MTD, N-1, YTD N-1, évolution, évolution %, 12 mois glissants, moyenne mobile, dernière valeur connue | [time-intelligence](references/time-intelligence.md) |
| Ratios | Marge, marge %, part du total, part du parent, contribution | [ratios](references/ratios-classements.md#ratios) |
| Classements | Rang, Top N + Autres, ABC / Pareto | [classements](references/ratios-classements.md#classements) |
| Clients | Clients actifs, nouveaux, perdus | [clients](references/ratios-classements.md#clients) |
| Dynamique | Groupe de calcul temps, paramètre de champs, format dynamique | [time-intelligence](references/time-intelligence.md#groupe-de-calcul) |
| Interrupteurs | Plan / N-1, Haut / Bas, Mensuel / Cumul via tables déconnectées, titres et couleurs dynamiques | [interrupteurs](references/interrupteurs.md) |

## Règles de la bibliothèque

- Time intelligence : toujours via `Dim_Date[Date]`, jamais via une date de la table de faits.
- Masquer les valeurs futures : les mesures temps renvoient `BLANK()` au-delà de la dernière date de données (modèle `_dateMax` fourni).
- Les pourcentages sont des ratios (0.15) formatés `0.0 %`, pas des valeurs × 100.
- Pas de `FORMAT()` dans une mesure numérique.

## Requête de contrôle

À exécuter dans la vue Requête DAX de Desktop, DAX Studio ou via le MCP :

```dax
EVALUATE
SUMMARIZECOLUMNS (
    Dim_Date[Annee],
    Dim_Date[MoisNum],
    "CA HT", [CA HT],
    "CA HT N-1", [CA HT N-1],
    "Évol. %", [CA HT Évol. %]
)
ORDER BY Dim_Date[Annee], Dim_Date[MoisNum]
```
