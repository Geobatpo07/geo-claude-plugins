# Checklist de revue d'un modèle sémantique

À dérouler avant publication ou lors d'un audit. Signaler chaque écart avec : objet, règle, correction proposée.

## Modèle

- [ ] Schéma en étoile : chaque table de faits reliée à ses dimensions en 1→* (voir `powerbi-data-modeling`).
- [ ] Aucune relation bidirectionnelle non justifiée.
- [ ] Aucune relation plusieurs-à-plusieurs non justifiée.
- [ ] `Dim_Date` présente, continue, marquée comme table de dates ; Date/heure automatique désactivée.
- [ ] Pas de colonne calculée qui pourrait être faite en Power Query ou à la source.
- [ ] Colonnes inutilisées supprimées.

## Nommage et présentation

- [ ] Préfixes `Fact_` / `Dim_` / `_Mesures` respectés.
- [ ] Clés et colonnes techniques masquées.
- [ ] Mesures rangées en dossiers d'affichage.
- [ ] Toutes les mesures visibles ont une description et un format.
- [ ] `Sort by column` défini pour les libellés de mois, jours, catégories ordonnées.
- [ ] `Summarize by = None` sur les colonnes numériques non additives.

## DAX

- [ ] `DIVIDE` utilisé pour toutes les divisions.
- [ ] Pas de `FILTER(<table entière>)` dans `CALCULATE` quand un filtre de colonne suffit.
- [ ] Pas d'`IFERROR`.
- [ ] Mesures de base réutilisées (pas de duplication de logique).
- [ ] Time intelligence basée sur `Dim_Date` (voir `powerbi-dax-library`).

## Sécurité

- [ ] Rôles RLS testés.
- [ ] Aucun secret dans les paramètres ou expressions M.
- [ ] Étiquette de sensibilité appliquée.

## Exemple de mesure conforme

```dax
/// Marge brute en pourcentage du CA HT. Source : Fact_Ventes.
Marge brute % =
VAR _ca = [CA HT]
VAR _marge = [Marge brute]
RETURN
    DIVIDE ( _marge, _ca )
```

(Le commentaire `///` ne vaut description qu'en TMDL ; dans Power BI Desktop, renseigner la propriété **Description**.)
