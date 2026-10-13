# Time intelligence

Hypothèse : `Dim_Date` marquée comme table de dates, reliée à la date principale des faits. Remplacer `[Mesure]` par la mesure de base.

## Borne « pas de futur »

Réutilisée dans les mesures ci-dessous pour éviter d'afficher des cumuls sur des mois sans données.

```dax
_Date max ventes =
CALCULATE ( MAX ( Fact_Ventes[DateCommande] ), REMOVEFILTERS () )
```

## Cumuls

```dax
CA HT YTD =
IF (
    MIN ( Dim_Date[Date] ) <= [_Date max ventes],
    CALCULATE ( [CA HT], DATESYTD ( Dim_Date[Date] ) )
)
```

```dax
CA HT QTD =
CALCULATE ( [CA HT], DATESQTD ( Dim_Date[Date] ) )
```

```dax
CA HT MTD =
CALCULATE ( [CA HT], DATESMTD ( Dim_Date[Date] ) )
```

## Comparaison N-1

```dax
CA HT N-1 =
CALCULATE ( [CA HT], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
```

```dax
CA HT YTD N-1 =
CALCULATE ( [CA HT YTD], SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
```

```dax
CA HT Évol. =
VAR _n = [CA HT]
VAR _n1 = [CA HT N-1]
RETURN
    IF ( NOT ISBLANK ( _n ) && NOT ISBLANK ( _n1 ), _n - _n1 )
```

```dax
CA HT Évol. % =
VAR _n = [CA HT]
VAR _n1 = [CA HT N-1]
RETURN
    IF ( NOT ISBLANK ( _n ), DIVIDE ( _n - _n1, _n1 ) )
```

## Période glissante

```dax
CA HT 12 mois glissants =
VAR _fin = MAX ( Dim_Date[Date] )
RETURN
    IF (
        _fin <= [_Date max ventes],
        CALCULATE (
            [CA HT],
            DATESINPERIOD ( Dim_Date[Date], _fin, -12, MONTH )
        )
    )
```

```dax
CA HT moyenne mobile 3 mois =
VAR _fin = MAX ( Dim_Date[Date] )
VAR _periode = DATESINPERIOD ( Dim_Date[Date], _fin, -3, MONTH )
RETURN
    IF (
        _fin <= [_Date max ventes],
        AVERAGEX (
            CALCULATETABLE ( VALUES ( Dim_Date[AnneeMois] ), _periode ),
            CALCULATE ( [CA HT] )
        )
    )
```

## Cumul depuis l'origine

```dax
CA HT cumul =
VAR _fin = MAX ( Dim_Date[Date] )
RETURN
    CALCULATE (
        [CA HT],
        Dim_Date[Date] <= _fin,
        REMOVEFILTERS ( Dim_Date )
    )
```

## Dernière valeur connue

```dax
Dernier cours connu =
VAR _date =
    LASTNONBLANK ( Dim_Date[Date], [Cours] )
RETURN
    CALCULATE ( [Cours], _date )
```

## Groupe de calcul

Évite de dupliquer chaque mesure en YTD / N-1 / Évol. %. Table `CG_Temps`, colonne `Calcul temps`.

| Élément | Expression | Format |
|---|---|---|
| Actuel | `SELECTEDMEASURE ()` | — |
| YTD | `CALCULATE ( SELECTEDMEASURE (), DATESYTD ( Dim_Date[Date] ) )` | — |
| N-1 | `CALCULATE ( SELECTEDMEASURE (), SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )` | — |
| Évol. % | voir ci-dessous | `"0.0 %"` |

```dax
VAR _n = SELECTEDMEASURE ()
VAR _n1 = CALCULATE ( SELECTEDMEASURE (), SAMEPERIODLASTYEAR ( Dim_Date[Date] ) )
RETURN
    IF ( NOT ISBLANK ( _n ), DIVIDE ( _n - _n1, _n1 ) )
```

Les groupes de calcul s'appliquent à **toutes** les mesures : exclure les mesures déjà temporelles ou les ratios si nécessaire avec `ISSELECTEDMEASURE`.

## Paramètre de champs

Créé via Modélisation → Nouveau paramètre → Champs. Permet à l'utilisateur de choisir la mesure ou la dimension affichée. Nommer `Param_Indicateur` / `Param_Axe`.
