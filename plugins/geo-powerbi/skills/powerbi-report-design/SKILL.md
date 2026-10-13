---
name: powerbi-report-design
description: "Charte graphique et règles de conception des rapports Power BI : thème JSON (couleurs, polices), grille et mise en page, structure des pages, choix du bon visuel, titres et libellés, segments, infobulles, navigation et accessibilité (contraste, texte alternatif, ordre de tabulation). À utiliser pour planifier, créer, revoir ou harmoniser un rapport ou une page Power BI, en complément de powerbi-report-cli (mécanique PBIR). Triggers: rapport, report, page, dashboard, tableau de bord, charte, thème, theme, couleurs, mise en page, layout, visuel, graphique, accessibilité, design, maquette."
---

# Design des rapports

> Charte par défaut **À ADAPTER** (couleurs et polices de la marque). La mécanique des fichiers PBIR, la prévisualisation et la publication sont gérées par `powerbi-report-cli` (Microsoft). Les visuels HTML/SVG relèvent de `powerbi-html-visuals`.

## Processus

1. **Cadrer** : public, décisions à prendre, 3 à 5 questions auxquelles la page répond, fréquence de consultation.
2. **Plan de pages** : une page = un sujet. Proposer la liste des pages et, pour chacune, un croquis de zones (texte ou Mermaid) **avant** de créer des visuels ; attendre la validation.
3. **Appliquer le thème** [references/theme-geo.json](references/theme-geo.json) au rapport (Affichage → Thèmes → Parcourir).
4. **Construire** en suivant la grille et les règles ci-dessous.
5. **Contrôler** avec la checklist [references/checklist-accessibilite.md](references/checklist-accessibilite.md).

## Structure type d'une page (canevas 1280 × 720)

```
┌──────────────────────────────────────────────────────────────┐
│ Titre de la page · période · logo             [navigation]   │  bandeau 56 px
├──────────────────────────────────────────────────────────────┤
│ KPI 1   │ KPI 2   │ KPI 3   │ KPI 4                          │  ligne KPI ~120 px
├──────────────────────────────────────────────────────────────┤
│ Tendance (courbe / colonnes)        │ Répartition (barres)   │  zone principale
│                                     │                        │
├─────────────────────────────────────┴────────────────────────┤
│ Détail (table / matrice) ou visuel secondaire                │
└──────────────────────────────────────────────────────────────┘
Segments : bandeau horizontal sous le titre ou volet latéral repliable.
```

- **Grille de 8 px**, marges extérieures 16 px, espacement entre visuels 16 px.
- Lecture en **Z** : le plus important en haut à gauche ; détail en bas.
- **6 à 8 visuels** maximum par page (hors formes et textes).
- Alignement strict : mêmes hauteurs sur une ligne, mêmes largeurs dans une colonne.

## Choisir le visuel

| Question | Visuel | Éviter |
|---|---|---|
| Évolution dans le temps | Courbe (continu), histogramme groupé (périodes discrètes) | Secteurs |
| Comparaison de catégories | Barres horizontales triées | 3D, radar |
| Part d'un tout (≤ 5 parts) | Barres 100 %, anneau à la rigueur | Secteurs > 5 parts |
| Écart à un objectif | Carte KPI avec cible, barres avec ligne de référence | Jauges multiples |
| Corrélation | Nuage de points | Double axe non justifié |
| Valeurs précises | Table / matrice avec mise en forme conditionnelle sobre | Tableaux de 50 colonnes |
| Géographie | Carte remplie (choroplèthe) si les zones sont connues | Bulles superposées |

## Règles de forme

- **Titres de visuels = message ou question**, pas seulement le nom de la mesure (« CA mensuel vs N-1 »).
- Unité et période visibles (titre, sous-titre ou étiquette).
- Trier les barres par valeur décroissante sauf ordre naturel (mois, tranches).
- Axe des valeurs à partir de 0 pour les barres/colonnes.
- Couleur = information : la couleur d'accent sert à **mettre en évidence**, le reste en gris/neutre. Rouge/vert réservés aux écarts (bon/mauvais), toujours doublés d'un signe ou d'une icône.
- Étiquettes de données plutôt que quadrillage quand il y a peu de points ; supprimer bordures, ombres et fonds superflus.
- Nombres abrégés (k, M) dans les KPI et axes ; précision complète en infobulle.

## Interactions et navigation

- Segments : 3 à 5 maximum par page, synchronisés seulement si nécessaire ; afficher les filtres actifs dans le sous-titre (mesure DAX de type texte).
- Boutons de navigation entre pages et signets pour les vues prédéfinies ; bouton « Réinitialiser les filtres ».
- Extraction (drill-through) vers une page de détail plutôt que des tables géantes.
- Infobulles de rapport pour le contexte (définition de la mesure, mini tendance).

## Livrables

- Plan de pages + croquis validés.
- Rapport avec thème appliqué.
- Checklist d'accessibilité complétée.
