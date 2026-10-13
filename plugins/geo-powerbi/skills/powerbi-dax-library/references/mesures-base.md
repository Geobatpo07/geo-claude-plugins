# Mesures de base

```dax
CA HT =
SUM ( Fact_Ventes[Montant HT] )
```

```dax
Quantité =
SUM ( Fact_Ventes[Quantite] )
```

```dax
Coût =
SUMX ( Fact_Ventes, Fact_Ventes[Quantite] * Fact_Ventes[Cout unitaire] )
```

```dax
Nb commandes =
DISTINCTCOUNT ( Fact_Ventes[NumeroCommande] )
```

```dax
Nb clients =
DISTINCTCOUNT ( Fact_Ventes[CustomerKey] )
```

En cas de SCD type 2, compter la clé métier : `DISTINCTCOUNT ( Dim_Client[CustomerCode] )` dans un contexte filtré par les faits :

```dax
Nb clients (SCD2) =
CALCULATE (
    DISTINCTCOUNT ( Dim_Client[CustomerCode] ),
    Fact_Ventes
)
```

```dax
Panier moyen =
DIVIDE ( [CA HT], [Nb commandes] )
```

```dax
Prix moyen pondéré =
DIVIDE ( [CA HT], [Quantité] )
```

```dax
Nb lignes =
COUNTROWS ( Fact_Ventes )
```

Valeur de stock (semi-additive : dernière date de la période, pas une somme) :

```dax
Stock fin de période =
VAR _derniereDate =
    LASTNONBLANK ( Dim_Date[Date], CALCULATE ( COUNTROWS ( Fact_Stocks ) ) )
RETURN
    CALCULATE ( SUM ( Fact_Stocks[Quantite] ), _derniereDate )
```
