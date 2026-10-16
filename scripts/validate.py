#!/usr/bin/env python3
"""Contrôle de cohérence du dépôt — usage : python scripts/validate.py"""
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
errors, warnings = [], []


def read_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        errors.append(f"{path} : JSON invalide ({exc})")
        return None


def parse_frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text.lstrip("﻿"), re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if kv:
            fm[kv.group(1)] = re.sub(r"^[\"']|[\"']$", "", kv.group(2)).strip()
    return fm


def main():
    market = read_json(os.path.join(ROOT, ".claude-plugin", "marketplace.json"))
    if market:
        if not KEBAB.match(market.get("name") or ""):
            errors.append(f"marketplace.json : nom \"{market.get('name')}\" non kebab-case")
        seen = set()
        for p in market.get("plugins", []):
            label = f"plugin \"{p.get('name')}\""
            if p.get("name") in seen:
                errors.append(f"{label} : déclaré deux fois")
            seen.add(p.get("name"))
            if not KEBAB.match(p.get("name") or ""):
                errors.append(f"{label} : nom non kebab-case")
            if not SEMVER.match(p.get("version") or ""):
                errors.append(f"{label} : version \"{p.get('version')}\" non SemVer")
            pdir = os.path.normpath(os.path.join(ROOT, p.get("source") or ""))
            if not os.path.isdir(pdir):
                errors.append(f"{label} : source introuvable ({p.get('source')})")
                continue
            manifest = read_json(os.path.join(pdir, ".claude-plugin", "plugin.json"))
            if manifest:
                if manifest.get("name") != p.get("name"):
                    errors.append(f"{label} : plugin.json name = \"{manifest.get('name')}\"")
                if manifest.get("version") != p.get("version"):
                    errors.append(f"{label} : version marketplace ({p.get('version')}) ≠ plugin.json "
                                  f"({manifest.get('version')})")
            docs_cmds = [os.path.join(pdir, "commands", f) for f in sorted(os.listdir(os.path.join(pdir, "commands")))
                         if f.endswith("-docs.md")] if os.path.isdir(os.path.join(pdir, "commands")) else []
            docs_text = "".join(open(f, encoding="utf-8-sig").read() for f in docs_cmds)
            if os.path.isdir(os.path.join(pdir, "commands")):
                for cf in sorted(os.listdir(os.path.join(pdir, "commands"))):
                    if cf.endswith(".md") and parse_frontmatter(open(os.path.join(pdir, "commands", cf),
                                                                      encoding="utf-8-sig").read()) is None:
                        errors.append(f"{label} : commande {cf} sans frontmatter (description)")
            skills_dir = os.path.join(pdir, "skills")
            if not os.path.isdir(skills_dir):
                warnings.append(f"{label} : aucun dossier skills/")
                continue
            for s in sorted(os.listdir(skills_dir)):
                sdir = os.path.join(skills_dir, s)
                if not os.path.isdir(sdir):
                    continue
                slabel = f"skill \"{p.get('name')}/{s}\""
                skill_file = os.path.join(sdir, "SKILL.md")
                if not os.path.isfile(skill_file):
                    errors.append(f"{slabel} : SKILL.md manquant")
                    continue
                with open(skill_file, encoding="utf-8-sig") as f:
                    text = f.read()
                fm = parse_frontmatter(text)
                if fm is None:
                    errors.append(f"{slabel} : frontmatter manquant")
                    continue
                name = fm.get("name") or ""
                if name != s:
                    errors.append(f"{slabel} : name \"{name}\" ≠ nom du dossier")
                if not KEBAB.match(name) or len(name) > 64:
                    errors.append(f"{slabel} : name invalide")
                desc = fm.get("description")
                if not desc:
                    errors.append(f"{slabel} : description manquante")
                elif len(desc) > 1024:
                    errors.append(f"{slabel} : description > 1024 caractères")
                lines = len(text.splitlines())
                if lines > 300:
                    warnings.append(f"{slabel} : {lines} lignes (> 300, déplacer vers references/)")
                if docs_cmds and f"`{s}`" not in docs_text:
                    errors.append(f"{slabel} : absent de la commande de documentation ({os.path.basename(docs_cmds[0])})")
                for ref in re.findall(r"\]\((references/[^)#\s]+)\)", text):
                    if not os.path.exists(os.path.join(sdir, ref)):
                        errors.append(f"{slabel} : lien cassé {ref}")

    for w in warnings:
        print(f"⚠  {w}", file=sys.stderr)
    for e in errors:
        print(f"✖  {e}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} erreur(s).", file=sys.stderr)
        return 1
    print(f"✔  Dépôt valide{f' ({len(warnings)} avertissement(s))' if warnings else ''}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
