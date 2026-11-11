# Fiche de cadrage — modèle de `CADRAGE.md`

À remplir **avec** le demandeur, par blocs de 3 à 5 questions. Ce qui n'a pas de réponse reste marqué `À CONFIRMER` : ne rien inventer. Aucune valeur réelle, aucun nom de personne physique hors propriétaires du projet, aucun identifiant de tenant ou d'espace de travail.

## Questions à poser

| Bloc | Questions |
|---|---|
| Public | Qui lit le rapport ? À quelle fréquence, sur quel support (écran, mobile, export PDF, réunion) ? Quel niveau de familiarité avec les chiffres ? |
| Décisions | Quelles décisions le rapport doit-il permettre de prendre ? Que fait le lecteur quand un chiffre est mauvais ? |
| Questions métier | Quelles sont les 3 à 7 questions auxquelles le rapport répond ? (une question = une phrase qui finit par « ? ») |
| Périmètre | Quelles entités, quelle période d'historique, quelles zones, quels produits ? Qu'est-ce qui est explicitement **hors périmètre** ? |
| Sources | D'où viennent les données (système, base, fichier) ? Qui en est propriétaire ? Sont-elles fiables, complètes, documentées ? |
| Grain | Que représente une ligne de chaque source (une ligne de commande, un jour × magasin…) ? À quel niveau le lecteur veut-il descendre ? |
| Fraîcheur | À quelle heure les données doivent-elles être à jour ? Quelle fréquence d'actualisation ? Quel retard est acceptable ? |
| Sécurité | Qui a le droit de voir quoi ? Données personnelles ou sensibles ? Filtrage par périmètre (région, service) ? |
| Succès | À quoi saura-t-on que le rapport est réussi ? Quel rapport ou fichier remplace-t-il ? |

Les réponses « grain » alimentent `powerbi-data-modeling` ; « sécurité » alimente `powerbi-governance` ; « fraîcheur » alimente `powerbi-alm` et `powerbi-performance`.

## Modèle

```markdown
# Cadrage — <nom du projet>

**Demandeur** : <rôle ou équipe>
**Propriétaire métier** : <rôle ou équipe> — signe la recette (`powerbi-testing`)
**Propriétaire technique** : <rôle ou équipe>
**Date** : <aaaa-mm-jj>
**Statut** : brouillon | validé le <aaaa-mm-jj> par <rôle>

## Public

- <Qui>, <fréquence>, <support>.

## Décisions à prendre

- <Décision que le rapport éclaire>.

## Questions métier

| # | Question | Page prévue | KPI |
|---|---|---|---|
| Q1 | <Question ?> | <page> | K-001, K-002 |

## Périmètre

- **Inclus** : <entités, période d'historique, zones>.
- **Hors périmètre** : <ce qui ne sera pas fait, et pourquoi>.

## Sources

| Source | Contenu | Grain | Propriétaire | Fiabilité |
|---|---|---|---|---|
| <système> | <tables / fichiers> | <une ligne = …> | <rôle> | <connue / À CONFIRMER> |

## Fraîcheur et actualisation

- Données à jour à <heure>, actualisation <fréquence>, retard toléré <durée>.

## Sécurité

- Niveau de sensibilité : <public / interne / confidentiel — À ADAPTER>.
- Données personnelles : <oui / non ; lesquelles>.
- Filtrage par périmètre : <règle en clair> (détail dans `SECURITE.md`).

## Critères de succès

- <Critère vérifiable : « les 5 questions ont une réponse en moins de 3 clics »>.

## Points ouverts

| # | Point | Qui décide | Échéance |
|---|---|---|---|
| 1 | <À CONFIRMER : …> | <rôle> | <aaaa-mm-jj> |
```

## Règles

- Une **question métier sans KPI** ou un **KPI sans question** est un signal : le reprendre avec le demandeur.
- Le cadrage est **validé explicitement** (date et rôle dans `Statut`) avant de modéliser. Toute modification ultérieure du périmètre est une nouvelle décision, datée.
- Trois à sept questions par rapport ; au-delà, proposer de scinder en plusieurs rapports ou plusieurs lots.
