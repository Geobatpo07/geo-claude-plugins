#!/usr/bin/env python3
"""Installe les skills d'un plugin dans un projet BI pour l'agent de son choix.

Usage :
  python scripts/install.py --agent <agent> [--target <dossier du projet>] [options]
  python scripts/install.py --list

Agents : claude, codex, gemini, grok, copilot, cursor, generic (voir --list pour les dossiers).
Options :
  --target <dossier>   projet BI où installer (défaut : dossier courant)
  --global             installer dans le dossier personnel (~/…) au lieu du projet ; pas d'AGENTS.md
  --dest <dossier>     dossier des skills imposé (remplace celui de l'agent)
  --plugin <nom>       plugin à installer (défaut : le seul plugin du dépôt)
  --skills a,b,c       n'installer que ces skills
  --no-agents-md       ne pas écrire le bloc d'index dans AGENTS.md
  --force              remplacer un skill du même nom qui n'a pas été installé par ce script
  --uninstall          retirer ce que ce script a installé (skills, sous-agents, bloc AGENTS.md)
  --dry-run            afficher ce qui serait fait, sans rien écrire

Les skills suivent le format ouvert « Agent Skills » (dossier + SKILL.md) : ils sont copiés tels quels.
Pour les agents qui ne chargent pas les skills eux-mêmes, le bloc AGENTS.md sert d'index :
il dit quel SKILL.md lire avant quelle tâche.
"""
import json
import os
import shutil
import sys

from common import ROOT, load_plugin, plugin_names, read_text, short_description, utf8_console, write_text

# agent → (dossier des skills dans le projet, dossier des skills personnel, bloc AGENTS.md par défaut)
AGENTS = {
    "claude": (".claude/skills", "~/.claude/skills", False),
    "codex": (".agents/skills", "~/.agents/skills", True),
    "gemini": (".agents/skills", "~/.agents/skills", True),
    "grok": (".grok/skills", "~/.grok/skills", True),
    "copilot": (".github/skills", "~/.copilot/skills", True),
    "cursor": (".cursor/skills", "~/.cursor/skills", True),
    "generic": (".agents/skills", "~/.agents/skills", True),
}
BEGIN = "<!-- {plugin}:début — bloc généré par scripts/install.py, ne pas modifier à la main -->"
END = "<!-- {plugin}:fin -->"


def agents_md_block(plugin, skills, rel_dest):
    lines = [
        BEGIN.format(plugin=plugin["name"]),
        f"## Skills Power BI — {plugin['name']} {plugin['version']}",
        "",
        f"Ce projet embarque des règles maison pour Power BI dans `{rel_dest}/`. Chaque skill est un dossier",
        "avec un `SKILL.md` (instructions) et des `references/` (détails, à lire seulement si nécessaire).",
        "",
        "**Avant d'agir sur le modèle sémantique, le DAX ou le rapport** : repérer ci-dessous le ou les skills",
        "concernés, lire leur `SKILL.md` en entier, puis appliquer. Si l'agent charge déjà ces skills",
        "automatiquement, ce bloc ne sert que d'index.",
        "",
        "Règles communes :",
        "",
        "- Lecture seule par défaut : plan, puis validation explicite avant toute suppression, tout renommage",
        "  et toute modification de relation ou de rôle de sécurité.",
        "- Projet sous Git, arbre propre avant d'écrire ; jamais de `git push` ni de publication sans demande.",
        "- Ne jamais lire ni versionner `.pbi/cache.abf` (données) ni `.pbi/localSettings.json`.",
        "- Ne jamais affirmer qu'une mesure a été vérifiée si aucune requête n'a été exécutée.",
        "",
        "| Skill | Quand le lire | Fichier |",
        "|---|---|---|",
    ]
    for s in skills:
        desc = short_description(s["description"]).replace("|", "\\|")
        lines.append(f"| `{s['name']}` | {desc} | `{rel_dest}/{s['name']}/SKILL.md` |")
    lines += ["", END.format(plugin=plugin["name"]), ""]
    return "\n".join(lines)


def update_agents_md(path, plugin_name, block, dry):
    """Remplace le bloc existant, ou l'ajoute à la fin ; block=None retire le bloc."""
    begin, end = BEGIN.format(plugin=plugin_name), END.format(plugin=plugin_name)
    text = read_text(path).replace("\r\n", "\n") if os.path.isfile(path) else ""
    i, j = text.find(begin), text.find(end)
    if i != -1 and j > i:
        before, after = text[:i].rstrip("\n"), text[j + len(end):].lstrip("\n")
    elif block is None:
        return
    else:
        before, after = text.rstrip("\n"), ""
    parts = [p for p in (before, block.rstrip("\n") if block else None, after.rstrip("\n")) if p]
    if not text and block:
        parts.insert(0, "# AGENTS.md\n\nInstructions pour les agents de code qui travaillent sur ce projet BI.")
    new = "\n\n".join(parts) + "\n"
    print(f"  {'[simulation] ' if dry else ''}AGENTS.md : bloc {plugin_name} "
          f"{'retiré' if block is None else 'écrit'} ({path})")
    if not dry:
        write_text(path, new)


def parse_args(argv):
    opts = {"agent": None, "target": os.getcwd(), "dest": None, "plugin": None, "skills": None,
            "global": False, "agents_md": None, "force": False, "uninstall": False, "dry": False, "list": False}
    flags = {"--global": "global", "--force": "force", "--uninstall": "uninstall", "--dry-run": "dry",
             "--list": "list"}
    values = {"--agent": "agent", "--target": "target", "--dest": "dest", "--plugin": "plugin",
              "--skills": "skills"}
    it = iter(argv)
    for a in it:
        if a in flags:
            opts[flags[a]] = True
        elif a == "--no-agents-md":
            opts["agents_md"] = False
        elif a in values:
            v = next(it, None)
            if v is None:
                raise SystemExit(f"✖  {a} attend une valeur.")
            opts[values[a]] = v
        elif a in ("-h", "--help"):
            print(__doc__)
            raise SystemExit(0)
        else:
            raise SystemExit(f"✖  Option inconnue : {a}\n{__doc__}")
    return opts


def main(argv):
    utf8_console()
    o = parse_args(argv)
    if o["list"]:
        print("Agent     Skills (projet)    Skills (personnel)    Bloc AGENTS.md")
        for name, (proj, home, block) in AGENTS.items():
            print(f"{name:<9} {proj:<18} {home:<21} {'oui' if block else 'non'}")
        return 0
    if o["agent"] not in AGENTS:
        print(f"✖  --agent requis : {', '.join(AGENTS)} (ou --list).", file=sys.stderr)
        return 2
    names = plugin_names()
    pname = o["plugin"] or (names[0] if len(names) == 1 else None)
    if pname not in names:
        print(f"✖  --plugin requis parmi : {', '.join(names)}.", file=sys.stderr)
        return 2
    plugin = load_plugin(pname)
    proj_dir, home_dir, block_default = AGENTS[o["agent"]]
    target = os.path.abspath(os.path.expanduser(o["target"]))
    if o["global"]:
        base, rel_dest = os.path.expanduser("~"), home_dir[2:]
    else:
        base, rel_dest = target, proj_dir
        if not os.path.isdir(target):
            print(f"✖  Dossier cible introuvable : {target}", file=sys.stderr)
            return 2
        if (target + os.sep).lower().startswith((ROOT + os.sep).lower()):
            print("✖  La cible est ce dépôt de skills : indiquer le projet BI avec --target.", file=sys.stderr)
            return 2
    dest = os.path.abspath(os.path.expanduser(o["dest"])) if o["dest"] else os.path.join(base, *rel_dest.split("/"))
    if o["dest"]:
        rel_dest = os.path.relpath(dest, base).replace(os.sep, "/")
    write_block = (block_default if o["agents_md"] is None else o["agents_md"]) and not o["global"]
    agents_dest = os.path.join(base, ".claude", "agents") if o["agent"] == "claude" else None
    manifest_path = os.path.join(dest, f".{pname}-manifest.json")
    previous = json.loads(read_text(manifest_path)) if os.path.isfile(manifest_path) else {}
    dry, tag = o["dry"], "[simulation] " if o["dry"] else ""

    def remove_previous():
        """Retire ce que la dernière installation avait posé (et rien d'autre)."""
        for s in previous.get("skills", []):
            p = os.path.join(dest, s)
            if os.path.isfile(os.path.join(p, "SKILL.md")):
                if o["uninstall"]:
                    print(f"  {tag}retiré : {p}")
                if not dry:
                    shutil.rmtree(p)
        for a in previous.get("agents", []):
            p = os.path.join(agents_dest or "", a + ".md")
            if agents_dest and os.path.isfile(p):
                if o["uninstall"]:
                    print(f"  {tag}retiré : {p}")
                if not dry:
                    os.remove(p)

    if o["uninstall"]:
        if not previous:
            print(f"Rien à retirer : aucun manifeste dans {dest}.")
            return 0
        remove_previous()
        if not dry:
            os.remove(manifest_path)
        if not o["global"]:
            update_agents_md(os.path.join(target, "AGENTS.md"), pname, None, dry)
        print(f"✔  {pname} retiré de {dest}.")
        return 0

    wanted = set(o["skills"].split(",")) if o["skills"] else None
    skills = [s for s in plugin["skills"] if wanted is None or s["name"] in wanted]
    unknown = (wanted or set()) - {s["name"] for s in skills}
    if unknown or not skills:
        print(f"✖  Skill(s) inconnu(s) : {', '.join(sorted(unknown)) or '(aucun skill)'}.", file=sys.stderr)
        return 2
    foreign = [s["name"] for s in skills
               if os.path.exists(os.path.join(dest, s["name"])) and s["name"] not in previous.get("skills", [])]
    if foreign and not o["force"]:
        print(f"✖  Déjà présent dans {dest} sans avoir été installé par ce script : {', '.join(foreign)}.\n"
              "   Vérifier leur contenu, puis relancer avec --force pour les remplacer.", file=sys.stderr)
        return 1

    print(f"{tag}{pname} {plugin['version']} → {dest} (agent : {o['agent']})")
    remove_previous()
    for s in skills:
        p = os.path.join(dest, s["name"])
        print(f"  {tag}skill : {s['name']}")
        if not dry:
            if os.path.exists(p):
                shutil.rmtree(p)
            shutil.copytree(s["dir"], p, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".gitkeep"))
    agents = plugin["agents"] if agents_dest else []
    for a in agents:
        print(f"  {tag}sous-agent : {a['name']}")
        if not dry:
            os.makedirs(agents_dest, exist_ok=True)
            shutil.copyfile(a["path"], os.path.join(agents_dest, a["name"] + ".md"))
    if not dry:
        write_text(manifest_path, json.dumps(
            {"plugin": pname, "version": plugin["version"], "agent": o["agent"],
             "skills": [s["name"] for s in skills], "agents": [a["name"] for a in agents]},
            ensure_ascii=False, indent=2) + "\n")
    if write_block:
        update_agents_md(os.path.join(target, "AGENTS.md"), pname, agents_md_block(plugin, skills, rel_dest), dry)
    print(f"✔  {len(skills)} skill(s){f', {len(agents)} sous-agent(s)' if agents else ''} "
          f"{'à installer' if dry else 'installé(s)'}.")
    if o["agent"] == "claude":
        print("   Sous Claude Code, préférer la marketplace (mises à jour automatiques) :\n"
              "   claude plugin marketplace add Geobatpo07/geo-claude-plugins ; "
              f"claude plugin install {pname}@geo-collection")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
