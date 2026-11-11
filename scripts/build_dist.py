#!/usr/bin/env python3
"""Construit les archives distribuables dans dist/ (dossier ignoré par Git).

Usage : python scripts/build_dist.py [--out <dossier>] [--plugin <nom>]

Pour chaque plugin :
  dist/<skill>.zip                 un skill seul (téléversement dans une application qui accepte un skill .zip)
  dist/<plugin>-<version>.zip      tous les skills + sous-agents (à décompresser dans .agents/skills/, etc.)
  dist/<plugin>-<version>.md       tous les skills en un seul fichier Markdown, pour un agent sans accès
                                   aux fichiers (conversation web, projet, instructions personnalisées)
"""
import os
import sys
import zipfile

from common import ROOT, load_plugin, plugin_names, read_text, strip_frontmatter, utf8_console, write_text

SKIP = {"__pycache__", ".gitkeep"}
FIXED_DATE = (2020, 1, 1, 0, 0, 0)  # archives reproductibles


def files_of(folder):
    out = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP)
        for name in sorted(filenames):
            if name not in SKIP and not name.endswith(".pyc"):
                out.append(os.path.join(dirpath, name))
    return out


def add(zf, path, arcname):
    info = zipfile.ZipInfo(arcname.replace(os.sep, "/"), FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with open(path, "rb") as f:
        zf.writestr(info, f.read())


def single_file(plugin):
    """Tous les skills en un seul Markdown : SKILL.md puis références textuelles."""
    out = [f"# {plugin['name']} {plugin['version']} — skills Power BI en un seul fichier", "",
           "Règles maison pour Power BI. Avant d'agir, repérer la section du skill concerné et l'appliquer.",
           "Les scripts Python (`scripts/`) ne sont pas inclus : ils demandent un agent avec accès aux fichiers.", ""]
    for s in plugin["skills"]:
        out += ["", "---", "", f"<!-- skill: {s['name']} -->", f"> **Quand l'utiliser** : {s['description']}", "",
                strip_frontmatter(read_text(os.path.join(s["dir"], "SKILL.md"))).strip(), ""]
        for path in files_of(os.path.join(s["dir"], "references")):
            rel = os.path.relpath(path, s["dir"]).replace(os.sep, "/")
            ext = os.path.splitext(path)[1].lower()
            if ext == ".md":
                out += ["", f"<!-- {s['name']}/{rel} -->", read_text(path).strip(), ""]
            elif ext in (".json", ".html", ".svg", ".dax", ".tmdl", ".yml", ".yaml"):
                out += ["", f"<!-- {s['name']}/{rel} -->", f"```{ext[1:]}", read_text(path).strip(), "```", ""]
    return "\n".join(out) + "\n"


def main(argv):
    utf8_console()
    out_dir = os.path.join(ROOT, "dist")
    only = None
    it = iter(argv)
    for a in it:
        if a == "--out":
            out_dir = os.path.abspath(next(it))
        elif a == "--plugin":
            only = next(it)
        else:
            print(__doc__)
            return 0 if a in ("-h", "--help") else 2
    os.makedirs(out_dir, exist_ok=True)
    for name in plugin_names():
        if only and name != only:
            continue
        plugin = load_plugin(name)
        base = f"{name}-{plugin['version']}"
        with zipfile.ZipFile(os.path.join(out_dir, base + ".zip"), "w") as bundle:
            for s in plugin["skills"]:
                with zipfile.ZipFile(os.path.join(out_dir, s["name"] + ".zip"), "w") as zf:
                    for path in files_of(s["dir"]):
                        rel = os.path.join(s["name"], os.path.relpath(path, s["dir"]))
                        add(zf, path, rel)
                        add(bundle, path, os.path.join("skills", rel))
            for a in plugin["agents"]:
                add(bundle, a["path"], os.path.join("agents", a["name"] + ".md"))
        write_text(os.path.join(out_dir, base + ".md"), single_file(plugin))
        print(f"✔  {name} {plugin['version']} : {len(plugin['skills'])} skill(s) .zip, {base}.zip, {base}.md "
              f"→ {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
