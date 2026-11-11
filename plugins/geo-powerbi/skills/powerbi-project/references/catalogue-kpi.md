# Catalogue de KPI — modèle de `KPI.md`

`KPI.md` est la **définition métier de référence** de chaque indicateur : ce que le métier a validé, indépendamment du DAX. Le code de la mesure reste dans le modèle ; le catalogue technique des mesures (généré depuis le modèle) relève de `powerbi-documentation`.

## Statuts

| Statut | Signification | Qui le fait passer |
|---|---|---|
| `proposé` | Définition rédigée par l'agent ou l'analyste, pas encore validée | — |
| `validé` | Définition, formule et seuils approuvés par le propriétaire | **L'utilisateur / le propriétaire du KPI** |
| `implémenté` | Mesure créée dans le modèle **et** valeur contrôlée (`powerbi-testing`) | L'agent, après vérification |
| `abandonné` | Retiré du périmètre ; garder l'entrée et la raison | L'utilisateur |

Seul un KPI `validé` peut être implémenté. Changer la définition d'un KPI `implémenté` le fait repasser à `proposé` jusqu'à nouvelle validation.

## Modèle

```markdown
# Catalogue de KPI — <nom du projet>

| ID | KPI | Statut | Mesure | Propriétaire |
|---|---|---|---|---|
| K-001 | Chiffre d'affaires HT | implémenté | `[CA HT]` | Direction commerciale |
| K-002 | Taux de marge brute | validé | `[Marge brute %]` | Direction financière |

## K-001 — Chiffre d'affaires HT

- **Statut** : implémenté
- **Question métier** : Q1 (voir `CADRAGE.md`)
- **Définition métier** : montant hors taxes des ventes facturées sur la période, nettes des avoirs.
- **Formule en clair** : somme des montants HT des lignes de facture − somme des avoirs.
- **Inclus / exclus** : inclut les ventes inter-sites ; exclut les commandes non facturées.
- **Mesure DAX cible** : `[CA HT]`
- **Grain** : ligne de facture ; analysable par jour, client, produit.
- **Déclinaisons** : N-1, cumul annuel, évolution % (même définition, mesures dérivées)
- **Source** : <système de facturation>, table des lignes de facture.
- **Propriétaire** : <rôle ou équipe>
- **Cible / seuils** : cible = budget de la période ; alerte sous 90 % de la cible — À ADAPTER.
- **Sens favorable** : hausse
- **Format** : montant sans décimale (voir `powerbi-conventions`)
- **Validé le** : <aaaa-mm-jj> par <rôle>
```

## Règles

- Identifiants `K-001`, `K-002`… **jamais réutilisés**, même après abandon.
- **Définition métier** : une phrase compréhensible sans connaître le modèle. **Formule en clair** : en mots, sans DAX.
- **Inclus / exclus** : c'est là que se cachent les désaccords (avoirs, taxes, inter-sociétés, annulations, périodes incomplètes). Poser la question plutôt que supposer.
- **Mesure DAX cible** : nom conforme à `powerbi-conventions` ; chercher d'abord un motif existant dans `powerbi-dax-library`.
- **Cible / seuils** et **sens favorable** : fournis par le propriétaire ; à défaut, laisser `À CONFIRMER` — ne pas inventer de seuil.
- Un KPI dérivé (N-1, cumul, évolution %) **n'a pas sa propre entrée** : il hérite de la définition du KPI de base ; le noter sur la ligne « Déclinaisons » si utile.
- Aucune valeur réelle dans ce fichier.
