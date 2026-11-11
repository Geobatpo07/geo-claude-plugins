# Definition of done par livrable

Un livrable est **terminé** quand tous ses contrôles sont vrais. Cette page dit **quoi vérifier et où est la règle** ; elle ne recopie pas les règles. Un contrôle non satisfait et accepté = une entrée `D-xxx` dans `DETTE.md` (`powerbi-lean`), jamais un oubli silencieux.

## Cadrage — `CADRAGE.md`, `KPI.md`

| Contrôle | Règle dans |
|---|---|
| Public, décisions et 3 à 7 questions métier renseignés | `powerbi-project` (fiche de cadrage) |
| Chaque question a au moins un KPI, chaque KPI une question | `powerbi-project` (catalogue de KPI) |
| Aucun `À CONFIRMER` bloquant ; points ouverts datés et attribués | `powerbi-project` |
| Cadrage et KPI **validés** par le demandeur (date et rôle) | `powerbi-project` |

## Modèle sémantique — `*.SemanticModel`

| Contrôle | Règle dans |
|---|---|
| Schéma en étoile, grain de chaque fait documenté, table de dates marquée | `powerbi-data-modeling` |
| Nommage, masquage, `summarizeBy`, descriptions, formats | `powerbi-conventions` |
| TMDL valide, projet rouvert sans erreur dans Desktop | `powerbi-tmdl` |
| Mode de stockage choisi et justifié ; cardinalités maîtrisées | `powerbi-data-modeling`, `powerbi-performance` |

## Mesures

| Contrôle | Règle dans |
|---|---|
| Chaque KPI `validé` a sa mesure ; statut passé à `implémenté` | `powerbi-project` (catalogue de KPI) |
| Motifs standard réutilisés plutôt que réécrits | `powerbi-dax-library` |
| Description, commentaire, dossier d'affichage, format | `powerbi-conventions` |
| Aucun anti-pattern DAX connu | `powerbi-performance` |
| Valeur contrôlée par un test | `powerbi-testing` |

## Maquette

| Contrôle | Règle dans |
|---|---|
| Construite à partir du modèle réel ; chaque élément étiqueté avec son champ | `powerbi-mockup` |
| Mesures manquantes listées, puis créées ou retirées de la page | `powerbi-mockup` |
| Validée par le demandeur avant toute construction | `powerbi-project` |

## Rapport — `*.Report`

| Contrôle | Règle dans |
|---|---|
| Chaque page répond aux quatre questions ; grille, thème, titres | `powerbi-report-design` |
| Accessibilité (contraste, texte alternatif, ordre de tabulation) | `powerbi-report-design` |
| Visuels HTML / SVG conformes et lisibles | `powerbi-html-visuals` |
| Temps de chargement des pages acceptable | `powerbi-performance` |

## Tests et recette — `tests/`, `tests/RECETTE.md`

| Contrôle | Règle dans |
|---|---|
| Tests des mesures et rapprochement avec la source passants | `powerbi-testing` |
| Sécurité testée par rôle | `powerbi-testing`, `powerbi-governance` |
| Recette signée par le métier | `powerbi-testing` |

## Publication

| Contrôle | Règle dans |
|---|---|
| Revue `powerbi-lean` : verdict *prêt à commit* | `powerbi-lean` |
| `SECURITE.md` à jour : rôles, accès, sensibilité | `powerbi-governance` |
| `DICTIONNAIRE.md` et note de version à jour | `powerbi-documentation` |
| Branche fusionnée, déploiement par l'environnement prévu, retour arrière possible | `powerbi-alm` |
| `MODIFICATIONS.md` complété ; dette restante consignée | `powerbi-lean` |

## Exploitation

| Contrôle (récurrent) | Règle dans |
|---|---|
| Actualisations réussies et dans le délai du cadrage | `powerbi-alm`, `powerbi-performance` |
| Dette revue ; échéances dépassées traitées ou replanifiées | `powerbi-lean` |
| Toute évolution repasse par cadrage → KPI → maquette si elle ajoute une question métier | `powerbi-project` |
