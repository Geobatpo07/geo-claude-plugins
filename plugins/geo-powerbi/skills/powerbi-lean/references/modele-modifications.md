# Modèle de MODIFICATIONS.md

Journal des modifications du projet, à la racine (à côté du `.pbip` et de `DETTE.md`), versionné avec le projet. **Plus récent en haut.** Il se remplit à mesure que la dette diminue : chaque dette soldée y a son entrée ; les évolutions hors dette (nouvelle page, nouvelle mesure) y sont aussi consignées.

```markdown
# Journal des modifications — <nom du projet>

## M-002 · 2026-10-20 · Fusion des mesures en doublon
- **Dette** : D-001 (soldée)
- **Type** : refactorisation
- **Objets modifiés** : `Mesures[012.Attendus]` réécrite pour référencer `[011.Approvisionne]`
- **Avant → après** : deux expressions DAX identiques → une mesure de base + une référence
- **Impact rapport** : aucun visuel modifié (vérifié avec `lean.py usage`)
- **Vérification** : valeurs comparées avant/après sur 3 périodes et 2 réseaux : identiques
- **Commit** : message `M-002: …` · **Par** : <nom>

## M-001 · 2026-10-15 · Table de dates marquée
- **Dette** : D-006 (soldée)
- **Type** : correction
- **Objets modifiés** : `Calendar` (dataCategory: Time, isKey sur DateValue)
- **Avant → après** : table non marquée → table de dates officielle
- **Impact rapport** : mesures `Cumul …` revérifiées
- **Vérification** : totaux mensuels identiques ; cumuls identiques
- **Commit** : message `M-001: …` · **Par** : <nom>
```

## Règles

- Identifiants **M-001, M-002…** jamais réutilisés. `python lean.py dette <projet>` donne le prochain.
- **Dette** : un ou plusieurs `D-xxx`, ou « hors dette ». Une dette citée ici doit être déplacée dans « Soldé » de `DETTE.md` avec `**Modification** : M-xxx`.
- **Type** : correction · refactorisation · nettoyage · performance · nouvelle fonctionnalité · documentation.
- **Vérification** : décrire ce qui a été comparé et le verdict (identique / écart expliqué). **Ne jamais recopier de valeurs réelles** (chiffres d'indicateurs, noms de patients ou d'institutions si sensibles).
- **Commit** : le message de commit commence par l'identifiant (`M-002: fusion des doublons`) ; `git log --grep "M-002"` retrouve le commit sans avoir à recopier son hash.
- Une modification = un commit qui contient le changement du modèle/rapport **et** les mises à jour de `DETTE.md` et `MODIFICATIONS.md`.
