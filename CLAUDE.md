# Instructions pour éditer ce dépôt

Ce dépôt est une **marketplace Claude Code** (`geo-collection`) qui contient des skills personnalisés pour Power BI / Fabric. Il complète `microsoft/skills-for-fabric`, qui n'est jamais modifié ici.

## Règles de structure

- Un skill = un dossier `plugins/<plugin>/skills/<nom>/` contenant `SKILL.md` (+ `references/` optionnel).
- Frontmatter obligatoire : `name` (= nom du dossier, kebab-case, ≤ 64 caractères) et `description` (≤ 1024 caractères, dit **quand** utiliser le skill, mots-clés FR + EN).
- `SKILL.md` < 300 lignes. Les détails vont dans `references/*.md`, cités par chemin relatif depuis `SKILL.md`.
- Un skill ne référence **jamais** un fichier hors de son plugin : seul le dossier du plugin est copié à l'installation.
- Pas de doublon de contenu entre skills : renvoyer vers le skill qui fait foi (ex. « appliquer `powerbi-conventions` »).

## Documentation

- Tout skill ajouté, renommé ou modifié dans son usage doit être reflété dans `plugins/<plugin>/commands/<plugin>-docs.md` (sections `skills` et `exemples`). `validate.py` refuse un skill absent du guide.

## Versionnement

- Toute modification d'un skill ⇒ incrémenter `version` (SemVer) dans `plugins/<plugin>/.claude-plugin/plugin.json`, puis `python scripts/generate_marketplace.py` pour resynchroniser `.claude-plugin/marketplace.json` (sinon le workflow GitHub le fait après le push).
  - correctif / reformulation : patch (1.0.0 → 1.0.1)
  - nouveau skill ou nouvelle règle : mineur (1.0.1 → 1.1.0)
  - règle supprimée ou inversée : majeur (1.1.0 → 2.0.0)
- Ajouter une entrée datée dans `CHANGELOG.md`.
- Lancer `python scripts/validate.py` avant chaque commit.
- Langages du dépôt : **Python** (scripts, bibliothèque standard uniquement, 3.8+) et **Markdown**. Pas de Node, pas de dépendance externe.

## Contenu

- Langue : français ; noms d'objets techniques et code (DAX, TMDL, M, JSON) en anglais ou selon les conventions définies dans `powerbi-conventions`.
- Marquer **« À ADAPTER »** toute valeur par défaut qui n'est pas encore une règle validée par l'équipe.
- Ne jamais inclure d'identifiants de tenant, d'espaces de travail, de jetons ou de données clients.
- Le DAX et le TMDL donnés en exemple doivent être syntaxiquement valides.
