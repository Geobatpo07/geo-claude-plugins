---
name: powerbi-lean
description: "Sobriété et revue des modèles et rapports Power BI : moins d'objets, pas moins de documentation. Trois modes : review (revue du git diff d'un projet PBIP), audit (mesures et colonnes inutilisées, doublons DAX, valeurs en dur, FILTER sur table entière, summarizeBy, clés visibles, table de dates) et dette (registre DETTE.md des raccourcis assumés). Inclut un script Python en lecture seule (lean.py) qui inventorie aussi les champs utilisés par le rapport avant un renommage. Triggers: revue, review, audit, nettoyage, simplifier, inutilisé, unused, doublon, duplicate, dette technique, tech debt, refactoriser, avant renommage, où est utilisée cette mesure, impact."
---

# powerbi-lean — moins d'objets, pas moins de documentation

But : chaque mesure, colonne ou table doit **servir une question** du rapport. On retire le superflu (doublons, objets morts, valeurs en dur, logique recopiée) ; on **ne retire jamais** descriptions, commentaires QUOI / COMMENT / ADAPTER, dossiers d'affichage ni formats.

Applique `powerbi-conventions` (validation, Git, modèle existant, confidentialité), `powerbi-performance` (réécritures DAX) et `powerbi-dax-library` (motifs de remplacement). **Lecture seule par défaut** : aucun changement sans plan validé.

## Le script

`scripts/lean.py` (dans le dossier de ce skill, Python 3.8+, bibliothèque standard uniquement) analyse un projet PBIP **sans rien modifier** : TMDL du modèle + PBIR du rapport.

```bash
python "<dossier du skill>/scripts/lean.py" audit "<dossier du projet PBIP>"            # audit complet
python "<dossier du skill>/scripts/lean.py" audit "<dossier>" --changed                  # fichiers modifiés depuis le dernier commit
python "<dossier du skill>/scripts/lean.py" usage "<dossier>"                            # champs utilisés par page / visuel
python "<dossier du skill>/scripts/lean.py" usage "<dossier>" --field "'Table'[Colonne]" # où un champ est utilisé
python "<dossier du skill>/scripts/lean.py" usage "<dossier>" --field "[Mesure]"
```

Ajouter `--json` pour une sortie exploitable. Sous Windows, utiliser `python` (ou `py`) ; ailleurs `python3`. Le dossier peut être celui du `.pbip`, du `*.SemanticModel` ou le fichier `.pbip`. Ce que le script vérifie et ses limites : [references/regles-audit.md](references/regles-audit.md).

Toujours **exécuter le script** plutôt que deviner l'utilisation d'un champ : c'est lui qui fait foi pour « utilisé / inutilisé ».

## Mode `review` — revue d'un changement

Quand : après une modification du modèle ou du rapport, avant le commit.

1. `git status` et `git diff` dans le dossier du projet (TMDL et PBIR).
2. `lean.py audit <dossier> --changed` : constats limités aux fichiers modifiés.
3. Relire le diff avec la grille [references/grille-review.md](references/grille-review.md) : logique dupliquée, mesure qui réécrit une mesure existante, valeur en dur, documentation retirée, renommage sans mise à jour des visuels, `lineageTag` copié.
4. Rendre **au plus 7 constats**, classés par impact : objet, problème, correction proposée (avec DAX si utile). Terminer par un verdict : *prêt à commit* / *à corriger*.
5. Ne rien modifier sans accord.

## Mode `audit` — revue de tout le projet

Quand : prise en main d'un modèle, avant une refonte, avant publication.

1. `lean.py audit <dossier>` (+ `usage` si des renommages sont envisagés).
2. Compléter par la lecture ciblée de ce que le script ne voit pas : logique quasi dupliquée (mêmes calculs avec variations), mesures « fourre-tout » (SWITCH qui recopie d'autres mesures), noms trompeurs.
3. Restituer un tableau **priorisé gain / risque** :
   - **Sans impact visuel** d'abord : table de dates, `summarizeBy`, masquage des clés, formats, descriptions.
   - **Nettoyage** : suppression d'objets inutilisés (après confirmation qu'aucun autre rapport connecté ne les utilise), fusion des doublons.
   - **Refactorisation** : mesures recopiées → composition de mesures de base ; valeurs en dur → mesures ou tables de référence.
   - **Renommages** en dernier, avec l'inventaire `usage` de chaque objet.
4. Proposer de consigner dans `DETTE.md` ce qui ne sera pas corrigé tout de suite.

## Mode `dette` — registre des raccourcis

Un raccourci assumé (valeur en dur temporaire, mesure dupliquée en attendant une refonte, contournement d'un problème de source) est consigné dans **`DETTE.md` à la racine du projet**, à côté du `.pbip` — **jamais en commentaire dans le modèle publié**.

- Ajouter : une entrée par raccourci avec le modèle [references/modele-dette.md](references/modele-dette.md).
- Lister : lire `DETTE.md`, regrouper par priorité et échéance, signaler les échéances dépassées.
- Solder : quand le raccourci est corrigé, déplacer l'entrée dans « Soldé » avec la date et le commit.
- À la fin d'un `audit`, proposer d'ajouter les constats non traités.

## Règles

- Supprimer ou fusionner seulement après inventaire `usage` **et** validation explicite.
- « Inutilisé » = non référencé par **ce** rapport : un autre rapport connecté au modèle publié peut l'utiliser. Le dire à chaque fois.
- Une simplification qui change un résultat n'est pas une simplification : vérifier les valeurs avant/après (requête DAX de contrôle).
- Jamais de commentaire `TODO` / `shortcut` dans les mesures : la dette va dans `DETTE.md`.
