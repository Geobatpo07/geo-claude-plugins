# Table de dates

## Exigences

- Une ligne par jour, **sans trou**, années complètes.
- Colonne `Date` de type date, unique → **Marquer comme table de dates**.
- Colonnes de tri (`MoisNum`, `JourSemaineNum`) liées aux libellés via *Sort by column*.
- Idéalement fournie par la source (Warehouse/Lakehouse) ; sinon Power Query ; DAX en dernier recours.

## Version DAX (table calculée)

```dax
Dim_Date =
VAR _debut =
    DATE (
        YEAR ( MIN ( MIN ( Fact_Ventes[DateCommande] ), MIN ( Fact_Ventes[DateLivraison] ) ) ),
        1,
        1
    )
VAR _fin =
    DATE (
        YEAR ( MAX ( MAX ( Fact_Ventes[DateCommande] ), MAX ( Fact_Ventes[DateLivraison] ) ) ),
        12,
        31
    )
RETURN
    ADDCOLUMNS (
        CALENDAR ( _debut, _fin ),
        "Annee", YEAR ( [Date] ),
        "Trimestre", "T" & QUARTER ( [Date] ),
        "MoisNum", MONTH ( [Date] ),
        "Mois", FORMAT ( [Date], "mmmm", "fr-FR" ),
        "AnneeMois", FORMAT ( [Date], "yyyy-mm" ),
        "JourSemaineNum", WEEKDAY ( [Date], 2 ),
        "JourSemaine", FORMAT ( [Date], "dddd", "fr-FR" ),
        "EstJourOuvre", WEEKDAY ( [Date], 2 ) <= 5
    )
```

Les bornes couvrent **toutes** les colonnes de date des faits utilisées dans le modèle (ici `DateCommande` et `DateLivraison`) : ajouter ou retirer une colonne dans les `MIN` / `MAX` selon les dates réellement reliées à `Dim_Date`. Avec la seule `DateCommande`, une livraison hors de cette plage n'aurait pas de ligne dans `Dim_Date`. À tester.

## Version Power Query (M)

```powerquery
let
    Debut = #date(2020, 1, 1),
    Fin = #date(Date.Year(DateTime.LocalNow()) + 1, 12, 31),
    Jours = Duration.Days(Fin - Debut) + 1,
    Liste = List.Dates(Debut, Jours, #duration(1, 0, 0, 0)),
    Table = Table.FromList(Liste, Splitter.SplitByNothing(), {"Date"}),
    Typee = Table.TransformColumnTypes(Table, {{"Date", type date}}),
    Annee = Table.AddColumn(Typee, "Annee", each Date.Year([Date]), Int64.Type),
    MoisNum = Table.AddColumn(Annee, "MoisNum", each Date.Month([Date]), Int64.Type),
    Mois = Table.AddColumn(MoisNum, "Mois", each Date.MonthName([Date], "fr-FR"), type text),
    Trimestre = Table.AddColumn(Mois, "Trimestre", each "T" & Text.From(Date.QuarterOfYear([Date])), type text),
    JourNum = Table.AddColumn(Trimestre, "JourSemaineNum", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    Jour = Table.AddColumn(JourNum, "JourSemaine", each Date.DayOfWeekName([Date], "fr-FR"), type text)
in
    Jour
```

Les bornes `2020` et `+1` sont **À ADAPTER** à l'historique réel.

## Exercice fiscal — À ADAPTER

Si l'exercice ne commence pas en janvier (ex. 1er octobre), ajouter `AnneeFiscale` et `MoisFiscalNum`, et passer la date de fin d'exercice aux fonctions de time intelligence : `DATESYTD ( Dim_Date[Date], "9/30" )` (format mois/jour ; vérifier selon la langue du modèle).
