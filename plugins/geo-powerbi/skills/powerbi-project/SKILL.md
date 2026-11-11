---
name: powerbi-project
description: "Cadrage et pilotage d'un projet BI Power BI de bout en bout : phases (cadrage, modélisation, mesures, maquette, rapport, recette, publication, exploitation), livrable et critère de sortie de chaque phase, skill qui fait foi, fiche de cadrage CADRAGE.md, catalogue de KPI KPI.md, rôles et definition of done. À charger au démarrage d'un projet ou d'un nouveau rapport, à la reprise d'un projet existant, pour savoir où en est un projet, quelle est la prochaine étape ou quel skill appliquer, et avant de livrer. Triggers: projet BI, cadrage, pilotage, besoin, exigences, requirements, kickoff, lancement, phases, planning, roadmap, livrable, deliverable, KPI, indicateur, catalogue de KPI, definition of done, avancement, prochaine étape, reprise de projet, onboarding, project management, BI lifecycle."
---

# powerbi-project — cadrer et piloter un projet BI

Ce skill est le **chef d'orchestre** : il dit **quoi faire, dans quel ordre et avec quel skill**. Il ne contient aucune règle technique : chaque phase renvoie au skill qui fait foi. Les skills Microsoft, s'ils sont installés (`semantic-model-authoring`, `powerbi-report-cli`), restent responsables de la **mécanique** (API, fichiers, MCP) ; sinon, Power BI Desktop ou le portail, par l'utilisateur.

## Règles

1. **Pas de modèle sans cadrage, pas de rapport sans maquette validée.** Une phase ne démarre que si le critère de sortie de la précédente est atteint, ou si l'écart est consigné dans `DETTE.md`.
2. **Les décisions métier appartiennent à l'utilisateur** : définition d'un KPI, seuil, cible, périmètre, règle de gestion, public. L'agent **propose** (avec options et conséquences), **ne tranche pas**, et note la décision dans `CADRAGE.md` ou `KPI.md`.
3. **Un KPI n'est implémenté que s'il est `validé`** dans `KPI.md`. Une mesure sans KPI ou sans question métier est un candidat à la suppression (`powerbi-lean`).
4. **Jamais de valeur réelle** ni de donnée personnelle dans `CADRAGE.md`, `KPI.md` ou tout autre fichier de pilotage : seulement des définitions, des noms d'objets et des ordres de grandeur fictifs.
5. Appliquer `powerbi-conventions` avant toute écriture (validation, Git, modèle existant, confidentialité).

## Les phases

| # | Phase | Objectif | Livrable | Skill qui fait foi | Critère de sortie |
|---|---|---|---|---|---|
| 1 | Cadrage | Savoir à qui sert le rapport et quelles décisions il éclaire | `CADRAGE.md`, `KPI.md` | `powerbi-project` | Questions métier et KPI **validés** par le demandeur |
| 2 | Modélisation | Schéma en étoile au bon grain | `*.SemanticModel` (TMDL) | `powerbi-data-modeling`, `powerbi-tmdl`, `powerbi-conventions` | Chaque KPI calculable ; relations et table de dates vérifiées |
| 3 | Mesures | Une mesure par KPI validé | Mesures décrites et rangées | `powerbi-dax-library`, `powerbi-performance` | Chaque `K-xxx` validé a sa mesure ; valeurs contrôlées |
| 4 | Maquette | Valider la page avant de la construire | Maquette HTML | `powerbi-mockup`, `powerbi-report-design` | Maquette validée ; aucune mesure manquante |
| 5 | Rapport | Construire les pages validées | `*.Report` (PBIR) | `powerbi-report-design`, `powerbi-html-visuals` | Pages conformes à la maquette et à la charte |
| 6 | Tests / recette | Prouver que les chiffres sont justes | `tests/`, `tests/RECETTE.md` | `powerbi-testing` | Recette signée par le métier |
| 7 | Publication | Livrer de façon sûre et réversible | `SECURITE.md`, `DICTIONNAIRE.md`, note de version | `powerbi-governance`, `powerbi-alm`, `powerbi-documentation` | Revue `powerbi-lean` *prêt à commit* ; sécurité testée ; déployé |
| 8 | Exploitation | Garder le rapport juste, rapide et sobre | `DETTE.md`, `MODIFICATIONS.md` à jour | `powerbi-lean`, `powerbi-performance` | Continu : dette suivie, actualisations surveillées |

Les phases 2 à 5 sont **itératives** : on livre une page complète (modèle → mesures → maquette → page) avant d'attaquer la suivante. Le détail des contrôles par livrable est dans [references/definition-of-done.md](references/definition-of-done.md).

## Arborescence type d'un projet

À la racine, à côté du `.pbip`, versionnés avec lui :

```
<projet>/
├── <Nom>.pbip
├── <Nom>.SemanticModel/      # modèle (TMDL)
├── <Nom>.Report/             # rapport (PBIR)
├── AGENTS.md                 # instructions pour les agents (skills à charger, garde-fous)
├── CADRAGE.md                # fiche de cadrage            → powerbi-project
├── KPI.md                    # catalogue de KPI            → powerbi-project
├── DICTIONNAIRE.md           # dictionnaire de données     → powerbi-documentation
├── RAPPORT.md                # fiche du rapport            → powerbi-documentation
├── NOTE-DE-VERSION.md        # notes de version            → powerbi-documentation
├── SECURITE.md               # rôles, accès, sensibilité   → powerbi-governance
├── DETTE.md                  # ce qui reste à corriger     → powerbi-lean
├── MODIFICATIONS.md          # ce qui a été fait           → powerbi-lean
└── tests/                    # tests et RECETTE.md         → powerbi-testing
```

Un fichier absent = une phase non faite : le dire, ne pas le créer vide « pour faire propre » (`PASSATION.md` ne s'écrit qu'à une passation).

## Processus

### Nouveau projet

1. **Interroger** l'utilisateur avec la fiche [references/fiche-cadrage.md](references/fiche-cadrage.md) — par blocs de 3 à 5 questions, pas tout d'un coup. Écrire `CADRAGE.md` ; marquer `À CONFIRMER` ce qui n'a pas de réponse, ne rien inventer.
2. **Dériver les KPI** des questions métier dans `KPI.md` ([references/catalogue-kpi.md](references/catalogue-kpi.md)), statut `proposé`. Faire valider chaque définition.
3. **Présenter le plan** : phases, livrables, ordre des pages, points ouverts. Attendre la validation.
4. Dérouler les phases en chargeant à chaque fois le skill qui fait foi ; à chaque fin de phase, vérifier le critère de sortie et mettre à jour le statut des KPI.

### Reprise d'un projet existant

1. **Audit en lecture seule d'abord** : `powerbi-lean` (mode `audit`), sans rien modifier.
2. **Situer le projet** dans les phases : quels fichiers de l'arborescence existent, lesquels sont à jour.
3. **Reconstituer** `CADRAGE.md` et `KPI.md` à partir de l'existant (pages, mesures, descriptions) : statut `implémenté` pour ce qui est en place, mais définition **à confirmer** par le métier — une mesure existante n'est pas une définition validée.
4. Consigner les écarts dans `DETTE.md` (`powerbi-lean`, mode `dette`) et proposer un plan priorisé. Les règles « modèle existant » de `powerbi-conventions` s'appliquent (pas de renommage d'office).

### Point d'avancement

À la demande (« où en est le projet ? ») : tableau phase / livrable / état (*fait*, *en cours*, *absent*) / prochain pas, nombre de KPI par statut, état de la dette (`lean.py dette`, voir `powerbi-lean`). Ne pas déclarer une phase terminée sans avoir vérifié son critère de sortie.

## Rôles

Un rôle = un périmètre, des skills à charger et des droits. Une même personne (ou un même agent) peut en tenir plusieurs, **mais pas auteur et relecteur du même changement**.

| Rôle | Phases | Skills à charger | Droits |
|---|---|---|---|
| Analyste cadrage | 1 | `powerbi-project` | Écrit `CADRAGE.md`, `KPI.md` ; lecture seule sur le modèle |
| Modeleur | 2 | `powerbi-data-modeling`, `powerbi-tmdl`, `powerbi-conventions`, `powerbi-governance` | Écrit `*.SemanticModel` |
| Développeur DAX | 3 | `powerbi-dax-library`, `powerbi-performance`, `powerbi-conventions`, `powerbi-testing` | Écrit les mesures et `tests/` |
| Concepteur de rapport | 4, 5 | `powerbi-mockup`, `powerbi-report-design`, `powerbi-html-visuals` | Écrit les maquettes et `*.Report` ; lecture seule sur le modèle |
| Relecteur / auditeur | 6, 7, 8 | `powerbi-lean`, `powerbi-conventions`, `powerbi-performance`, `powerbi-governance`, `powerbi-testing`, `powerbi-alm`, `powerbi-documentation` | **Lecture seule** ; rend des constats et un verdict |

Si l'agent sait déléguer à des sous-agents et que ceux du plugin sont installés, trois d'entre eux tiennent ces rôles : `powerbi-auditeur` (lecture seule), `powerbi-modeleur` (modèle et mesures) et `powerbi-concepteur-rapport` (maquette et rapport). Sinon, l'agent applique les mêmes rôles en **chargeant les skills listés** et en respectant la colonne « Droits ».

## Références

- [references/fiche-cadrage.md](references/fiche-cadrage.md) — questions de cadrage et modèle de `CADRAGE.md`.
- [references/catalogue-kpi.md](references/catalogue-kpi.md) — modèle de `KPI.md`, statuts, règles de définition.
- [references/definition-of-done.md](references/definition-of-done.md) — contrôles par livrable, avec le skill qui fait foi.
