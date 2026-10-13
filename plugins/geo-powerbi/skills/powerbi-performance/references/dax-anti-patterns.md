# DAX — anti-patterns et réécritures

## 1. FILTER sur une table entière

Avant :

```dax
CA Web =
CALCULATE ( [CA HT], FILTER ( Fact_Ventes, Fact_Ventes[Canal] = "Web" ) )
```

Après :

```dax
CA Web =
CALCULATE ( [CA HT], Fact_Ventes[Canal] = "Web" )
```

Si le filtre doit **conserver** le filtre existant sur la colonne (intersection plutôt que remplacement) :

```dax
CA Web =
CALCULATE ( [CA HT], KEEPFILTERS ( Fact_Ventes[Canal] = "Web" ) )
```

## 2. Filtre sur une mesure : itérer la dimension, pas le fait

Avant :

```dax
CA gros clients =
CALCULATE ( [CA HT], FILTER ( Fact_Ventes, [CA HT] > 10000 ) )
```

Après (le seuil s'applique par client, sur la colonne de la dimension) :

```dax
CA gros clients =
CALCULATE (
    [CA HT],
    FILTER ( VALUES ( Dim_Client[CustomerKey] ), [CA HT] > 10000 )
)
```

## 3. Expressions répétées

Avant :

```dax
Évol. % =
IF ( [CA HT N-1] = 0, BLANK (), ( [CA HT] - [CA HT N-1] ) / [CA HT N-1] )
```

Après :

```dax
Évol. % =
VAR _n1 = [CA HT N-1]
RETURN
    DIVIDE ( [CA HT] - _n1, _n1 )
```

## 4. Existence

Avant :

```dax
A acheté = IF ( COUNTROWS ( FILTER ( Fact_Ventes, Fact_Ventes[Quantite] > 0 ) ) > 0, 1 )
```

Après :

```dax
A acheté =
IF ( NOT ISEMPTY ( CALCULATETABLE ( Fact_Ventes, Fact_Ventes[Quantite] > 0 ) ), 1 )
```

## 5. Densification par des zéros

Avant :

```dax
CA affiché = IF ( ISBLANK ( [CA HT] ), 0, [CA HT] )
```

Effet : chaque combinaison produit × client affiche une ligne → requêtes énormes.

Après : garder `[CA HT]` tel quel. Si l'affichage de 0 est demandé, limiter le 0 aux éléments **déjà présents** dans le contexte (ex. mois de la période sélectionnée) plutôt qu'à tout le produit cartésien :

```dax
CA affiché =
VAR _ca = [CA HT]
RETURN
    IF ( ISBLANK ( _ca ) && ISINSCOPE ( Dim_Date[AnneeMois] ), 0, _ca )
```

Ou utiliser l'option du visuel *Afficher les éléments sans données* sur l'axe concerné uniquement.

## 6. Itérateur sur le mauvais grain

Avant (itère chaque ligne de vente) :

```dax
Moyenne CA par client =
AVERAGEX ( Fact_Ventes, [CA HT] )
```

Après (itère les clients) :

```dax
Moyenne CA par client =
AVERAGEX ( VALUES ( Dim_Client[CustomerKey] ), [CA HT] )
```

## 7. SWITCH sur des mesures lourdes

`SWITCH ( TRUE (), … )` peut évaluer plusieurs branches. Pour sélectionner une mesure selon un segment, préférer un **paramètre de champs** ou un **groupe de calcul**.
