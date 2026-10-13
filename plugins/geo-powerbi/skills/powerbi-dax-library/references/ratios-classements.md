# Ratios, classements, clients

## Ratios

```dax
Marge brute =
[CA HT] - [Coût]
```

```dax
Marge brute % =
DIVIDE ( [Marge brute], [CA HT] )
```

Part du total général (ignore les filtres de la dimension produit) :

```dax
Part du CA % =
DIVIDE ( [CA HT], CALCULATE ( [CA HT], REMOVEFILTERS ( Dim_Produit ) ) )
```

Part du parent dans une hiérarchie (catégorie → sous-catégorie) :

```dax
Part dans la catégorie % =
DIVIDE (
    [CA HT],
    CALCULATE ( [CA HT], REMOVEFILTERS ( Dim_Produit[Sous-categorie] ) )
)
```

Part en conservant les filtres de segments (ALLSELECTED) :

```dax
Part du CA visible % =
DIVIDE ( [CA HT], CALCULATE ( [CA HT], ALLSELECTED ( Dim_Produit ) ) )
```

## Classements

```dax
Rang produit =
IF (
    ISINSCOPE ( Dim_Produit[Produit] ),
    RANKX ( ALLSELECTED ( Dim_Produit[Produit] ), [CA HT],, DESC, DENSE )
)
```

Top N + « Autres » : préférer le filtre visuel **Top N** natif. Si une ligne « Autres » est requise, créer une table déconnectée des libellés (produits + « Autres ») :

```dax
CA HT Top N =
VAR _n = 10
VAR _produit = SELECTEDVALUE ( Produits_TopN[Produit] )
VAR _top =
    TOPN ( _n, ALLSELECTED ( Dim_Produit[Produit] ), [CA HT] )
RETURN
    IF (
        _produit = "Autres",
        CALCULATE ( [CA HT], EXCEPT ( ALLSELECTED ( Dim_Produit[Produit] ), _top ) ),
        IF (
            _produit IN SELECTCOLUMNS ( _top, "p", Dim_Produit[Produit] ),
            CALCULATE ( [CA HT], Dim_Produit[Produit] = _produit )
        )
    )
```

Classe ABC (Pareto 80 / 15 / 5) :

```dax
Classe ABC =
VAR _ca = [CA HT]
VAR _total = CALCULATE ( [CA HT], ALLSELECTED ( Dim_Produit[Produit] ) )
VAR _cumul =
    SUMX (
        FILTER (
            ALLSELECTED ( Dim_Produit[Produit] ),
            [CA HT] >= _ca
        ),
        [CA HT]
    )
VAR _pct = DIVIDE ( _cumul, _total )
RETURN
    IF (
        ISINSCOPE ( Dim_Produit[Produit] ) && NOT ISBLANK ( _ca ),
        SWITCH ( TRUE (), _pct <= 0.8, "A", _pct <= 0.95, "B", "C" )
    )
```

(Coûteux sur de grandes dimensions : préférer un calcul en amont si > ~10 000 produits.)

## Clients

Clients actifs sur la période = `[Nb clients]`.

Nouveaux clients (premier achat dans la période) :

```dax
Nouveaux clients =
VAR _debut = MIN ( Dim_Date[Date] )
VAR _clientsPeriode = VALUES ( Fact_Ventes[CustomerKey] )
VAR _clientsAvant =
    CALCULATETABLE (
        VALUES ( Fact_Ventes[CustomerKey] ),
        Dim_Date[Date] < _debut,
        REMOVEFILTERS ( Dim_Date )
    )
RETURN
    COUNTROWS ( EXCEPT ( _clientsPeriode, _clientsAvant ) )
```

Clients perdus (actifs N-1, inactifs sur la période) :

```dax
Clients perdus =
VAR _clientsN1 =
    CALCULATETABLE (
        VALUES ( Fact_Ventes[CustomerKey] ),
        SAMEPERIODLASTYEAR ( Dim_Date[Date] )
    )
VAR _clientsN = VALUES ( Fact_Ventes[CustomerKey] )
RETURN
    COUNTROWS ( EXCEPT ( _clientsN1, _clientsN ) )
```

Si un historique long existe, matérialiser la date de premier achat dans `Dim_Client` (en amont) et comparer à la période : beaucoup plus rapide.
